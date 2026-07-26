import pytest

from piggy.core.categorization import is_internal_transfer_candidate, normalize_iban


def test_normalize_iban_strips_spaces_and_case():
    assert normalize_iban("de89 3704 0044 0532 0130 00") == "DE89370400440532013000"
    assert normalize_iban(None) is None
    assert normalize_iban("") is None


def test_internal_transfer_candidate_ignores_formatting():
    known = ["DE89370400440532013000"]
    assert is_internal_transfer_candidate("DE89 3704 0044 0532 0130 00", known)
    assert is_internal_transfer_candidate("de89370400440532013000", known)
    assert not is_internal_transfer_candidate("DE89370400440532013001", known)


@pytest.mark.asyncio
async def test_spaced_partner_iban_resolves_to_target_account(db):
    """
    A grouped IBAN used to pass the candidate check but miss the dict lookup,
    turning the booking into a transfer without a target account.
    """
    from datetime import date

    from piggy.core.bank_sync import _get_internal_accounts, _process_transaction
    from piggy.core.bank.fints_client import FinTSTransaction
    from piggy.models.database.account import Account
    from piggy.models.database.user import User, UserRole
    from piggy.core.auth import get_password_hash
    from piggy.models.database.transaction import TransactionType

    user = User(
        email="iban@example.com",
        hashed_password=get_password_hash("password"),
        name="Iban User",
        is_active=True,
        email_verified=True,
        role=UserRole.USER,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    source = Account(
        user_id=user.id, name="Source", type="Giro", iban="DE89370400440532013000"
    )
    partner = Account(
        user_id=user.id, name="Partner", type="Giro", iban="DE02120300000000202051"
    )
    db.add_all([source, partner])
    await db.commit()
    await db.refresh(partner)

    internal_accounts = await _get_internal_accounts(db)
    known_ibans = list(internal_accounts.keys())

    booking = FinTSTransaction(
        booking_date=date.today(),
        amount="-25.00",
        description="Rent share",
        partner_name="Partner",
        # Same account, but reported with grouping spaces and lowercase
        partner_iban="de02 1203 0000 0000 2020 51",
    )

    preview = await _process_transaction(
        booking, source.id, user.id, known_ibans, internal_accounts, db
    )

    assert preview is not None
    assert preview.type == TransactionType.TRANSFER
    assert preview.target_account_id == partner.id
