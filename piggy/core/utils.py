"""
Miscellaneous utility functions.
"""

import uuid
from datetime import date
from decimal import Decimal
from typing import Optional, List
from typing import Union
from uuid import UUID

from dateutil.relativedelta import relativedelta
from fastapi import HTTPException, status
from sqlalchemy import func, extract, and_, or_, exists, case
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.base import ExecutableOption

from piggy.core.i18n import _
from piggy.models.category import CategoryWithBudgets
from piggy.models.dashboard import BudgetStatus
from piggy.models.database.account import Account
from piggy.models.database.budget import Budget
from piggy.models.database.category import Category
from piggy.models.database.recurring_payment import RecurringInterval
from piggy.models.database.recurring_payment import (
    RecurringPayment as RecurringPaymentDB,
)
from piggy.models.database.transaction import (
    Transaction as TransactionDB,
    TransactionType,
)
from piggy.models.database.user import User


async def get_account_or_404(
    account_id: uuid.UUID, db: AsyncSession, user_id: uuid.UUID = None
) -> Account:
    """
    Retrieve an account by ID, optionally filtering by user ID.
    """
    query = select(Account).where(Account.id == account_id)
    if user_id:
        query = query.where(Account.user_id == user_id)

    result = await db.execute(query)

    if account := result.scalars().first():
        return account
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail=_("errors.account_not_found")
    )


async def get_budget_or_404(
    budget_id: uuid.UUID,
    db: AsyncSession,
) -> Budget:
    """Retrieve a budget by ID."""
    result = await db.execute(select(Budget).where(Budget.id == budget_id))
    budget = result.scalars().first()
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_("errors.budget_not_found")
        )
    return budget


async def get_category_or_404(
    category_id: uuid.UUID,
    db: AsyncSession,
    *,
    options: Union[ExecutableOption, None] = None,
) -> Union[Category, CategoryWithBudgets]:
    """Retrieve a category by ID."""

    query = select(Category)
    if options:
        query = query.options(options)
    query = query.where(Category.id == category_id)
    result = await db.execute(query)

    category = result.scalars().first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_("errors.category_not_found")
        )
    return category


async def get_recurring_payment_or_404(
    recurring_payment_id: uuid.UUID, db: AsyncSession, user_id: uuid.UUID
) -> RecurringPaymentDB:
    """Retrieve a recurring payment by ID."""
    result = await db.execute(
        select(RecurringPaymentDB).where(
            RecurringPaymentDB.id == recurring_payment_id,
            RecurringPaymentDB.user_id == user_id,
        )
    )
    payment = result.scalars().first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_("errors.recurring_payment_not_found"),
        )
    return payment


def get_next_recurring_payment_occurrence(
    start_date: date,
    interval: RecurringInterval,
    interval_x_days: Optional[int],
    compare: date,
) -> date:
    """Calculate the next occurrence of a recurring payment."""
    if interval == RecurringInterval.DAYS_X and not interval_x_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=_("errors.invalid_interval")
        )
    next_occurrence = start_date
    if next_occurrence >= compare:
        return next_occurrence

    while next_occurrence < compare:
        match interval:
            case RecurringInterval.DAILY:
                next_occurrence += relativedelta(days=1)
            case RecurringInterval.WEEKLY:
                next_occurrence += relativedelta(weeks=1)
            case RecurringInterval.MONTHLY:
                next_occurrence += relativedelta(months=1)
            case RecurringInterval.YEARLY:
                next_occurrence += relativedelta(years=1)
            case RecurringInterval.DAYS_X:
                next_occurrence += relativedelta(days=interval_x_days)
    return next_occurrence


async def calculate_balance(  # pylint: disable=too-many-arguments, too-many-positional-arguments,too-many-locals,too-many-branches,too-many-statements
    db: AsyncSession,
    current_user: Optional[User],
    transactions: List[TransactionDB],
    account_ids: set[UUID],
    today: date,
    current_month: bool,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Optional[Decimal]]:
    """Calculate monthly balance and prognosed balance."""
    balance_query = select(func.sum(Account.balance))
    if current_user:
        balance_query = balance_query.where(Account.user_id == current_user.id)

    balance_result = await db.execute(balance_query)
    balance = balance_result.scalar() or Decimal("0.00")
    monthly_income = Decimal("0.00")
    monthly_expenses = Decimal("0.00")
    prognosed_balance = None

    for transaction in transactions:
        if current_user:
            # Logic as in frontend
            is_source_mine = transaction.account_id in account_ids
            is_target_mine = (
                transaction.target_account_id in account_ids
                if transaction.target_account_id
                else False
            )
            match transaction.type:
                case TransactionType.INCOME:
                    monthly_income += transaction.amount
                case TransactionType.EXPENSE:
                    monthly_expenses += transaction.amount
                case TransactionType.TRANSFER:
                    if is_target_mine and not is_source_mine:
                        monthly_income += transaction.amount
                    elif is_source_mine and not is_target_mine:
                        monthly_expenses += transaction.amount
        else:
            match transaction.type:
                case TransactionType.INCOME:
                    monthly_income += transaction.amount
                case TransactionType.EXPENSE:
                    monthly_expenses += transaction.amount

    monthly_balance = monthly_income - monthly_expenses

    if current_month and current_user:
        prognosis_balance = monthly_balance
        start_of_current_month = date(today.year, today.month, 1)
        end_of_month = start_of_current_month + relativedelta(day=31)
        days_in_month = end_of_month.day
        days_left = days_in_month - today.day

        # Only compute prognosis if there are remaining days
        if days_left > 0:
            rec_query = select(RecurringPaymentDB).where(
                RecurringPaymentDB.user_id == current_user.id
            )
            rec_result = await db.execute(rec_query)
            recurring_payments = rec_result.scalars().all()

            # Add remaining recurring payments for the current month
            for rp in recurring_payments:
                is_source_mine = (
                    rp.account_id in account_ids if rp.account_id else False
                )
                is_target_mine = (
                    rp.target_account_id in account_ids
                    if rp.target_account_id
                    else False
                )
                next_occurrence = get_next_recurring_payment_occurrence(
                    rp.start_date,
                    rp.interval,
                    rp.interval_x_days,
                    today,
                )
                while next_occurrence <= end_of_month:
                    match rp.type:
                        case TransactionType.INCOME:
                            prognosis_balance += rp.amount
                        case TransactionType.EXPENSE:
                            prognosis_balance -= rp.amount
                        case TransactionType.TRANSFER:
                            if is_target_mine and not is_source_mine:
                                prognosis_balance += rp.amount
                            elif is_source_mine and not is_target_mine:
                                prognosis_balance -= rp.amount
                    next_occurrence = get_next_recurring_payment_occurrence(
                        rp.start_date,
                        rp.interval,
                        rp.interval_x_days,
                        next_occurrence + relativedelta(days=1),
                    )

            avg_var_balance = await get_past_transactions_average(
                db, current_user, start_of_current_month
            )

            prognosis_balance += (avg_var_balance / Decimal(days_in_month)) * Decimal(
                days_left
            )

        prognosed_balance = prognosis_balance

    return balance, monthly_income, monthly_expenses, monthly_balance, prognosed_balance


async def get_past_transactions_average(
    db: AsyncSession,
    current_user: User,
    start_date: Optional[date] = None,
    account_ids: Optional[set[UUID]] = None,
) -> Decimal:
    """Calculate the average amount of money spent in the past 6 months for the given accounts"""
    start_date = start_date or date.today()
    start_date_prognosis = start_date - relativedelta(months=6)

    month_col = extract("month", TransactionDB.timestamp)
    year_col = extract("year", TransactionDB.timestamp)

    if account_ids is None:
        account_ids = await get_account_ids(db, current_user)

    past_transactions_query = (
        select(
            func.sum(
                case(
                    (
                        TransactionDB.type == TransactionType.INCOME,
                        TransactionDB.amount,
                    ),
                    (
                        TransactionDB.type == TransactionType.EXPENSE,
                        -TransactionDB.amount,
                    ),
                    (
                        and_(
                            TransactionDB.type == TransactionType.TRANSFER,
                            TransactionDB.target_account_id.in_(account_ids),
                            ~TransactionDB.account_id.in_(account_ids),
                        ),
                        TransactionDB.amount,
                    ),
                    (
                        and_(
                            TransactionDB.type == TransactionType.TRANSFER,
                            TransactionDB.account_id.in_(account_ids),
                            ~TransactionDB.target_account_id.in_(account_ids),
                        ),
                        -TransactionDB.amount,
                    ),
                    else_=Decimal("0.00"),
                )
            )
        )
        .where(
            (TransactionDB.account_id.in_(account_ids))
            | (TransactionDB.target_account_id.in_(account_ids))
        )
        .where(
            (TransactionDB.timestamp >= start_date_prognosis)
            & (TransactionDB.timestamp < start_date)
        )
        .where(
            ~exists().where(
                and_(
                    RecurringPaymentDB.user_id == current_user.id,
                    TransactionDB.type == RecurringPaymentDB.type,
                    or_(
                        func.lower(TransactionDB.description).contains(
                            func.lower(RecurringPaymentDB.name)
                        ),
                        func.lower(RecurringPaymentDB.name).contains(
                            func.lower(TransactionDB.description)
                        ),
                    ),
                    func.abs(TransactionDB.amount - RecurringPaymentDB.amount)
                    <= (RecurringPaymentDB.amount * Decimal("0.10")),
                )
            )
        )
        .group_by(month_col, year_col)
    )

    past_transactions_result = await db.execute(past_transactions_query)
    monthly_balances = list(past_transactions_result.scalars().all())

    # Calculate average from aggregated results
    if monthly_balances:
        total_var_balance = sum(
            val if val else Decimal("0.00") for val in monthly_balances
        )
        num_months = len(monthly_balances)
        avg_var_balance = total_var_balance / Decimal(num_months)
    else:
        avg_var_balance = Decimal("0.00")

    return avg_var_balance


async def get_account_ids(
    db: AsyncSession, current_user: Optional[User] = None
) -> set[UUID]:
    """
    Returns a set of account IDs for the given user.
    If no user is provided, returns all account IDs.
    """
    query = select(Account.id)
    if current_user:
        query = query.where(Account.user_id == current_user.id)

    user_accounts_result = await db.execute(query)
    return set(r[0] for r in user_accounts_result.all())


async def get_transactions_of_month(
    db: AsyncSession, month: int, year: int, current_user: Optional[User] = None
) -> tuple[List[TransactionDB], set[UUID]]:
    """Returns transactions of a given month."""
    tx_filter = (extract("month", TransactionDB.timestamp) == month) & (
        extract("year", TransactionDB.timestamp) == year
    )
    user_account_ids: set[UUID] = set()
    if current_user:
        user_account_ids = await get_account_ids(db, current_user)
        tx_filter = tx_filter & (
            TransactionDB.account_id.in_(user_account_ids)
            | TransactionDB.target_account_id.in_(user_account_ids)
        )

    transaction_query = select(TransactionDB).where(tx_filter)
    transactions = await db.execute(transaction_query)
    return list(transactions.scalars().all()), set(user_account_ids)


async def get_budget_status(
    db: AsyncSession,
    current_user: Optional[User],
    transactions: List[TransactionDB],
) -> List[BudgetStatus]:
    """Get budget status for current user and transactions."""
    budget_statuses = []
    budget_query = select(Budget).options(joinedload(Budget.category))
    if current_user:
        budget_query = budget_query.where(
            or_(Budget.user_id == current_user.id, Budget.user_id.is_(None))
        )

    budget_result = await db.execute(budget_query)
    budgets = budget_result.scalars().all()

    all_accounts = await db.execute(select(Account.id, Account.user_id))
    account_user = {r[0]: r[1] for r in all_accounts.all()}

    for budget in budgets:
        if budget.user_id:
            spent = Decimal(
                sum(
                    abs(tx.amount)
                    for tx in transactions
                    if tx.category_id == budget.category_id
                    and tx.type == TransactionType.EXPENSE
                    and account_user.get(tx.account_id) == budget.user_id
                )
            )
        else:
            spent = Decimal(
                sum(
                    abs(tx.amount)
                    for tx in transactions
                    if tx.category_id == budget.category_id
                    and tx.type == TransactionType.EXPENSE
                )
            )

        budget_statuses.append(
            BudgetStatus(
                category_id=budget.category_id,
                category_name=budget.category.name,
                budget_amount=budget.amount,
                spent_amount=spent,
                user_id=budget.user_id,
            )
        )
    return budget_statuses


async def apply_transaction_effect(
    transaction: TransactionDB,
    user_id: uuid.UUID,
    db: AsyncSession,
    revert: bool = False,
):
    """apply transaction effect to account balance"""
    account = await get_account_or_404(transaction.account_id, db, user_id)
    amount = transaction.amount if not revert else -transaction.amount
    if transaction.type == TransactionType.INCOME:
        account.balance += amount
    elif transaction.type == TransactionType.EXPENSE:
        account.balance -= amount
    elif transaction.type == TransactionType.TRANSFER:
        account.balance -= amount
        if transaction.target_account_id:
            target_account = await get_account_or_404(transaction.target_account_id, db)
            target_account.balance += amount
    await db.commit()
