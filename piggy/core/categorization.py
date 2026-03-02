"""
Local categorization helper.

- If scikit-learn is available, uses TF-IDF + MultinomialNB per user.
- Otherwise, uses a simple keyword scoring heuristic based on past transactions and category names.

This module does not persist any model; it is trained on-the-fly from existing labeled data.
"""

import re
import uuid
from typing import Optional, Iterable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from piggy.models.database.account import Account as AccountDB
from piggy.models.database.category import Category as CategoryDB
from piggy.models.database.transaction import (
    Transaction as TransactionDB,
)


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


async def suggest_category_id(
    db: AsyncSession, user_id: uuid.UUID, description: str
) -> Optional[uuid.UUID]:
    """
    Suggest a category for a transaction description for a given user.
    Returns a category_id or None if not enough information.
    """
    # Fetch user's labeled transactions
    q = (
        (
            select(TransactionDB.description, TransactionDB.category_id)
            .where(TransactionDB.category_id.is_not(None))
            .join_from(TransactionDB, CategoryDB, isouter=True)
        )
        .join(AccountDB, AccountDB.id == TransactionDB.account_id)
        .where(AccountDB.user_id == user_id)
    )

    if rows := (await db.execute(q)).all():
        x = [_normalize(r[0]) for r in rows]
        y = [str(r[1]) for r in rows]

        # Try sklearn if available
        try:
            pipe = make_pipeline(TfidfVectorizer(min_df=1), MultinomialNB())
            pipe.fit(x, y)
            return uuid.UUID(pipe.predict([_normalize(description)])[0])
        except Exception:  # pylint: disable=broad-exception-caught
            return None
    return None


def is_internal_transfer_candidate(
    partner_iban: Optional[str], known_ibans: Iterable[str]
) -> bool:
    """Simple check whether a partner IBAN is one of our known IBANs."""
    if not partner_iban:
        return False
    p = partner_iban.replace(" ", "").upper()
    return p in {iban.replace(" ", "").upper() for iban in known_ibans}
