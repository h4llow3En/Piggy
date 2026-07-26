"""
Local categorization helper.

- If scikit-learn is available, uses TF-IDF + MultinomialNB per user.
- Otherwise, uses a simple keyword scoring heuristic based on past transactions and category names.

This module does not persist any model; it is trained on-the-fly from existing labeled data.
"""

import re
import uuid
from typing import Callable, Optional, Iterable

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


CategoryPredictor = Callable[[str], Optional[uuid.UUID]]


async def build_category_classifier(
    db: AsyncSession, user_id: uuid.UUID
) -> Optional[CategoryPredictor]:
    """
    Train a category classifier once and return a predictor for it.

    Training loads the user's entire labeled history, so callers that classify
    more than one description must build the predictor once and reuse it
    instead of calling :func:`suggest_category_id` per item.

    Returns None if there is nothing to learn from.
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

    rows = (await db.execute(q)).all()
    if not rows:
        return None

    x = [_normalize(r[0]) for r in rows]
    y = [str(r[1]) for r in rows]

    try:
        pipe = make_pipeline(TfidfVectorizer(min_df=1), MultinomialNB())
        pipe.fit(x, y)
    except Exception:  # pylint: disable=broad-exception-caught
        return None

    def predict(description: str) -> Optional[uuid.UUID]:
        try:
            return uuid.UUID(pipe.predict([_normalize(description)])[0])
        except Exception:  # pylint: disable=broad-exception-caught
            return None

    return predict


async def suggest_category_id(
    db: AsyncSession, user_id: uuid.UUID, description: str
) -> Optional[uuid.UUID]:
    """
    Suggest a category for a single transaction description.

    Trains a throwaway model, so only use this for one-off lookups.
    """
    predictor = await build_category_classifier(db, user_id)
    return predictor(description) if predictor else None


def normalize_iban(iban: Optional[str]) -> Optional[str]:
    """
    Normalize an IBAN for comparison.

    Banks report IBANs with or without grouping spaces, so every comparison and
    every dict lookup has to go through this.
    """
    if not iban:
        return None
    return iban.replace(" ", "").upper()


def is_internal_transfer_candidate(
    partner_iban: Optional[str], known_ibans: Iterable[str]
) -> bool:
    """Simple check whether a partner IBAN is one of our known IBANs."""
    p = normalize_iban(partner_iban)
    if not p:
        return False
    return p in {normalize_iban(iban) for iban in known_ibans}
