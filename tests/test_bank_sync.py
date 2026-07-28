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


def _preview(account_id, ttype, amount, day, target_account_id=None):
    """Minimal preview, only the fields the mirror matching looks at."""
    from datetime import datetime, timezone
    from decimal import Decimal

    from piggy.models.transaction import BankTransactionPreview

    return BankTransactionPreview(
        account_id=account_id,
        target_account_id=target_account_id,
        description="Umbuchung",
        amount=Decimal(amount),
        type=ttype,
        timestamp=datetime(2026, 7, day, tzinfo=timezone.utc),
        is_potential_duplicate=False,
    )


def test_credit_leg_without_partner_iban_is_dropped():
    """
    The bank reports the IBAN on the debit leg only, so the credit leg reaches
    the batch as plain income and used to double the amount.
    """
    import uuid

    from piggy.core.bank_sync import _drop_mirrored_credit_legs
    from piggy.models.database.transaction import TransactionType

    a, b = uuid.uuid4(), uuid.uuid4()
    debit = _preview(a, TransactionType.TRANSFER, "100.00", 1, target_account_id=b)
    # Booked a day later, as an over night clearing would
    credit = _preview(b, TransactionType.INCOME, "100.00", 2)

    assert _drop_mirrored_credit_legs([debit, credit]) == [debit]


def test_real_income_is_kept():
    """Income without a matching transfer, and income that does not line up."""
    import uuid

    from piggy.core.bank_sync import _drop_mirrored_credit_legs
    from piggy.models.database.transaction import TransactionType

    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

    salary = _preview(b, TransactionType.INCOME, "100.00", 1)
    assert _drop_mirrored_credit_legs([salary]) == [salary]

    debit = _preview(a, TransactionType.TRANSFER, "100.00", 1, target_account_id=b)
    # Right amount, but lands on a different account
    elsewhere = _preview(c, TransactionType.INCOME, "100.00", 1)
    # Right account, but booked far outside the clearing window
    much_later = _preview(b, TransactionType.INCOME, "100.00", 20)
    # Right account and date, but a different amount
    other_amount = _preview(b, TransactionType.INCOME, "250.00", 1)

    kept = _drop_mirrored_credit_legs([debit, elsewhere, much_later, other_amount])
    assert kept == [debit, elsewhere, much_later, other_amount]


def test_each_transfer_swallows_only_one_credit_leg():
    """A payment that happens to look like the counter booking must survive."""
    import uuid

    from piggy.core.bank_sync import _drop_mirrored_credit_legs
    from piggy.models.database.transaction import TransactionType

    a, b = uuid.uuid4(), uuid.uuid4()
    debit = _preview(a, TransactionType.TRANSFER, "100.00", 1, target_account_id=b)
    counter_booking = _preview(b, TransactionType.INCOME, "100.00", 1)
    coincidence = _preview(b, TransactionType.INCOME, "100.00", 1)

    kept = _drop_mirrored_credit_legs([debit, counter_booking, coincidence])
    assert len(kept) == 2
    assert kept[0] == debit


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


@pytest.mark.asyncio
async def test_sync_fetches_accounts_of_every_household_member(db, test_user, second_user):
    """
    A login may serve a joint account or one registered under another member.
    Narrowing the fetch to the connection owner made those bookings vanish.
    """
    from datetime import date

    from piggy.core.bank_sync import _collect_previews
    from piggy.core.bank.fints_client import FinTSTransaction
    from piggy.models.database.account import Account
    from piggy.models.database.bank_connection import BankConnection

    own = Account(
        user_id=test_user.id, name="Own", type="Giro", iban="DE89370400440532013000"
    )
    partners = Account(
        user_id=second_user.id,
        name="Partner",
        type="Giro",
        iban="DE02120300000000202051",
    )
    db.add_all([own, partners])
    await db.commit()
    await db.refresh(partners)

    conn = BankConnection(
        user_id=test_user.id, bank_code="12030000", login="tester", status="ready"
    )
    db.add(conn)
    await db.commit()

    class _Client:
        """Serves both accounts, as the real login would."""

        def __init__(self):
            self.requested = []

        def fetch_transactions(self, iban, start, end):
            self.requested.append(iban)
            return [
                FinTSTransaction(
                    booking_date=date.today(),
                    amount="-10.00",
                    description=f"Booking on {iban}",
                    partner_name="Shop",
                    partner_iban="DE44500105175407324931",
                )
            ]

    client = _Client()
    previews = await _collect_previews(
        client, conn, date.today(), date.today(), db
    )

    assert set(client.requested) == {
        "DE89370400440532013000",
        "DE02120300000000202051",
    }
    assert partners.id in {p.account_id for p in previews}


@pytest.mark.asyncio
async def test_internal_transfer_yields_exactly_one_preview(db, test_user):
    """End to end: a transfer between two own accounts must not also show up as income."""
    from datetime import date

    from piggy.core.bank_sync import _collect_previews
    from piggy.core.bank.fints_client import FinTSTransaction
    from piggy.models.database.account import Account
    from piggy.models.database.bank_connection import BankConnection
    from piggy.models.database.transaction import TransactionType

    iban_a = "DE89370400440532013000"
    iban_b = "DE02120300000000202051"

    a = Account(user_id=test_user.id, name="A", type="Giro", iban=iban_a)
    b = Account(user_id=test_user.id, name="B", type="Giro", iban=iban_b)
    db.add_all([a, b])
    await db.commit()
    await db.refresh(a)
    await db.refresh(b)

    conn = BankConnection(
        user_id=test_user.id, bank_code="12030000", login="tester", status="ready"
    )
    db.add(conn)
    await db.commit()

    class _Client:
        def fetch_transactions(self, iban, start, end):
            if iban == iban_a:
                return [
                    FinTSTransaction(
                        date.today(), "-100.00", "Umbuchung", "Felix", iban_b
                    )
                ]
            # The credit leg, reported without a partner IBAN
            return [
                FinTSTransaction(date.today(), "100.00", "Umbuchung", "Felix", None)
            ]

    previews = await _collect_previews(
        _Client(), conn, date.today(), date.today(), db
    )

    assert len(previews) == 1
    assert previews[0].type == TransactionType.TRANSFER
    assert previews[0].account_id == a.id
    assert previews[0].target_account_id == b.id


@pytest.mark.asyncio
async def test_sync_status_is_only_returned_to_its_owner(auth_client, second_user_auth, test_user):
    """A sync result holds raw bank data and must not be readable by task id alone."""
    import uuid as _uuid

    from piggy.core.bank_sync_cache import sync_task_cache
    from piggy.models.bank import SyncTaskStatus

    task_id = _uuid.uuid4()
    sync_task_cache.create_task(task_id, test_user.id)
    sync_task_cache.update_task(task_id, SyncTaskStatus.COMPLETED, result=[])

    own = await auth_client.get(f"/api/v1/bank/sync/status/{task_id}")
    assert own.status_code == 200

    other = await auth_client.get(
        f"/api/v1/bank/sync/status/{task_id}", headers=second_user_auth
    )
    assert other.status_code == 404
