"""
Miscellaneous functions to calculate statistics
"""

from collections import defaultdict, OrderedDict
from datetime import date
from decimal import Decimal

from sqlalchemy import select, func, case, and_, text, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import coalesce

from dateutil.relativedelta import relativedelta
from piggy.core.utils import get_past_transactions_average
from piggy.models.database.account import Account
from piggy.models.database.budget import Budget
from piggy.models.database.category import Category
from piggy.models.database.transaction import Transaction, TransactionType
from piggy.models.database.user import User
from piggy.models.statistic import (
    CategorySpendStatistics,
    CategorySpendItem,
    AccountBalanceStatistics,
    AccountBalanceItem,
    BudgetUsageStatistics,
    BudgetUsageItem,
    CashflowStatistics,
    MonthlyCashflowItem,
)



async def categories_spent_statistics(db: AsyncSession, current_user: User):
    """
    Retrieves category spend statistics for all users and the current user
    """
    start_of_month = date.today() + relativedelta(day=1)
    spent_statistic_query = (
        select(
            Category.name,
            func.date(Transaction.timestamp).label("date"),
            func.sum(Transaction.amount).label("amount_all"),
            func.sum(
                case(
                    (Account.user == current_user, Transaction.amount), else_=Decimal(0)
                )
            ).label("amount_user"),
        )
        .where(
            and_(
                Transaction.type == TransactionType.EXPENSE,
                Transaction.timestamp >= start_of_month,
            )
        )
        .join(Transaction.account)
        .join(Account.user)
        .join(Category, Category.id == Transaction.category_id)
        .group_by(Category.name, func.date(Transaction.timestamp))
    )

    spent_statistic_result = await db.execute(spent_statistic_query)
    spent_statistic_rows = list(spent_statistic_result.all())

    return _map_spend_statistics(spent_statistic_rows)


def _map_spend_statistics(statistic_rows: list):
    data = defaultdict(list)
    for category, date_val, amount_all, amount_user in statistic_rows:
        data[category].append(
            CategorySpendItem(date=date_val, amount=amount_all, amount_user=amount_user)
        )

    spent_statistic = []
    for category in sorted(data.keys()):
        items = sorted(data[category], key=lambda x: x.date)  # Sort by date
        spent_statistic.append(CategorySpendStatistics(name=category, items=items))

    return spent_statistic


async def balance_statistics(  # pylint: disable=too-many-locals
    db: AsyncSession, current_user: User
) -> list[AccountBalanceStatistics]:
    """
    Get account balance statistics for the current user.
    """
    start_date = date.today() + relativedelta(months=-1, day=1)
    current_date = date.today()

    # Get changes grouped by account and date
    combined_changes_stmt = (
        select(
            Transaction.account_id.label("account_id"),
            func.date(Transaction.timestamp).label("date"),
            func.sum(
                case(
                    (
                        Transaction.type == TransactionType.INCOME,
                        Transaction.amount,
                    ),
                    (
                        Transaction.type == TransactionType.EXPENSE,
                        -Transaction.amount,
                    ),
                    (
                        Transaction.type == TransactionType.TRANSFER,
                        -Transaction.amount,
                    ),
                    else_=Decimal("0.00"),
                )
            ).label("change"),
        )
        .where(func.date(Transaction.timestamp) >= start_date)
        .group_by(Transaction.account_id, func.date(Transaction.timestamp))
    ).union_all(
        select(
            Transaction.target_account_id.label("account_id"),
            func.date(Transaction.timestamp).label("date"),
            func.sum(Transaction.amount).label("change"),
        )
        .where(
            and_(
                Transaction.type == TransactionType.TRANSFER,
                Transaction.target_account_id.isnot(None),
                func.date(Transaction.timestamp) >= start_date,
            )
        )
        .group_by(Transaction.target_account_id, func.date(Transaction.timestamp))
    )

    combined_changes = combined_changes_stmt.subquery()

    grouped_changes_stmt = select(
        combined_changes.c.account_id,
        combined_changes.c.date,
        func.sum(combined_changes.c.change).label("change"),
    ).group_by(combined_changes.c.account_id, combined_changes.c.date)

    result = await db.execute(grouped_changes_stmt)
    changes = defaultdict(dict)
    for row in result.all():
        d = row.date
        if isinstance(d, str):
            d = date.fromisoformat(d)
        changes[row.account_id][d] = row.change

    # Get all accounts
    accounts_stmt = (
        select(Account, User.name.label("user_name"))
        .join(User, Account.user_id == User.id)
        .order_by(text("user_name"), Account.sort_order, Account.id)
    )
    accounts_result = await db.execute(accounts_stmt)
    accounts = accounts_result.all()

    last_day_of_month = current_date + relativedelta(day=31)

    output = []
    for acc_row in accounts:
        acc = acc_row[0]
        user_name = acc_row[1]

        acc_name = acc.name
        if acc.user_id != current_user.id:
            acc_name = f"{acc.name} ({user_name})"

        history = []
        curr_balance = acc.balance

        # We work backwards from today's balance
        # changes[acc.id] contains changes from start_date to today

        # Pre-calculate balances for each day by working backwards from current balance
        daily_balances = {}
        temp_balance = curr_balance

        # Iterate from today back to start_date
        d = current_date
        while d >= start_date:
            daily_balances[d] = temp_balance
            # The balance on day D is (Balance on day D+1) - (Change on day D+1)
            # Wait, no. Current balance is the balance *after* all transactions until now.
            # So Balance(D) = Balance(today) - Sum(Changes from D+1 to today)

            change = changes.get(acc.id, {}).get(d, Decimal(0))
            temp_balance -= change
            d -= relativedelta(days=1)

        # Now fill history in forward order
        d = start_date
        while d <= current_date:
            history.append(AccountBalanceItem(date=d, balance=daily_balances[d]))
            d += relativedelta(days=1)

        # Add prognosis (forward)
        avg_daily_change = await get_past_transactions_average(
            db, current_user, account_ids={acc.id}
        ) / Decimal(last_day_of_month.day)

        temp_prognosis_balance = curr_balance
        d = current_date + relativedelta(days=1)
        while d <= last_day_of_month:
            temp_prognosis_balance += avg_daily_change
            history.append(AccountBalanceItem(date=d, balance=temp_prognosis_balance))
            d += relativedelta(days=1)

        output.append(
            AccountBalanceStatistics(
                name=acc_name,
                own_account=acc.user_id == current_user.id,
                history=history,
            )
        )

    return output


async def budget_usage_statistics(
    db: AsyncSession, current_user: User, year: int, month: int
) -> BudgetUsageStatistics:
    """
    Get budget usage statistics for a specific year and month.
    """
    start_date = date(year, month, 1)
    end_date = start_date + relativedelta(months=1)

    total_spent_subquery = (
        select(
            Transaction.category_id,
            func.sum(Transaction.amount).label("total_spent"),
        )
        .where(
            and_(
                Transaction.timestamp >= start_date,
                Transaction.timestamp < end_date,
                Transaction.type == TransactionType.EXPENSE,
                Transaction.category_id.isnot(None),
            )
        )
        .group_by(Transaction.category_id)
        .subquery()
    )

    user_spent_subquery = (
        select(
            Transaction.category_id,
            func.sum(Transaction.amount).label("user_spent"),
        )
        .join(Account, Transaction.account_id == Account.id)
        .where(
            and_(
                Account.user_id == current_user.id,
                Transaction.timestamp >= start_date,
                Transaction.timestamp < end_date,
                Transaction.type == TransactionType.EXPENSE,
                Transaction.category_id.isnot(None),
            )
        )
        .group_by(Transaction.category_id)
        .subquery()
    )

    query = (
        select(
            Budget.category_id,
            Category.name,
            func.sum(Budget.amount).label("budget_amount"),
            coalesce(total_spent_subquery.c.total_spent, Decimal("0.00")).label(
                "total_spent"
            ),
            coalesce(user_spent_subquery.c.user_spent, Decimal("0.00")).label(
                "user_spent"
            ),
        )
        .join(Category, Budget.category_id == Category.id)
        .outerjoin(
            total_spent_subquery,
            Budget.category_id == total_spent_subquery.c.category_id,
        )
        .outerjoin(
            user_spent_subquery, Budget.category_id == user_spent_subquery.c.category_id
        )
        .group_by(
            Budget.category_id,
            Category.name,
            total_spent_subquery.c.total_spent,
            user_spent_subquery.c.user_spent,
        )
    )

    budget_items = []
    for row in (await db.execute(query)).all():
        budget_amount = row.budget_amount
        user_spent = row.user_spent
        total_spent = row.total_spent

        user_percentage = Decimal("0.00")
        if total_spent > 0:
            user_percentage = (user_spent / total_spent) * 100

        budget_items.append(
            BudgetUsageItem(
                category_id=str(row.category_id),
                category_name=row.name,
                budget_amount=budget_amount,
                total_spent=total_spent,
                user_spent=user_spent,
                user_percentage=user_percentage,
            )
        )

    return BudgetUsageStatistics(year=year, month=month, budgets=budget_items)


async def cashflow_statistics(
    db: AsyncSession, current_user: User
) -> CashflowStatistics:
    """
    Get monthly income vs expenses for the last 12 months for the current user.
    """
    # Calculate the range: 12 months ago until now
    end_date = date.today() + relativedelta(day=1, months=1)
    start_date = end_date + relativedelta(months=-12)

    query = (
        select(
            extract("year", Transaction.timestamp).label("year"),
            extract("month", Transaction.timestamp).label("month"),
            func.sum(
                case(
                    (Transaction.type == TransactionType.INCOME, Transaction.amount),
                    else_=Decimal("0.00"),
                )
            ).label("income"),
            func.sum(
                case(
                    (Transaction.type == TransactionType.EXPENSE, Transaction.amount),
                    else_=Decimal("0.00"),
                )
            ).label("expenses"),
        )
        .join(Account, Transaction.account_id == Account.id)
        .where(
            and_(
                Account.user_id == current_user.id,
                Transaction.timestamp >= start_date,
                Transaction.timestamp < end_date,
                Transaction.type.in_([TransactionType.INCOME, TransactionType.EXPENSE]),
            )
        )
        .group_by(text("year"), text("month"))
        .order_by(text("year"), text("month"))
    )

    result = await db.execute(query)

    cashflow_data = OrderedDict()
    curr = start_date
    while curr < end_date:
        key = (int(curr.year), int(curr.month))
        cashflow_data[key] = {"income": Decimal("0.00"), "expenses": Decimal("0.00")}
        curr += relativedelta(months=1)

    for row in result.all():
        key = (int(row.year), int(row.month))
        if key in cashflow_data:
            cashflow_data[key]["income"] = row.income
            cashflow_data[key]["expenses"] = row.expenses

    items = [
        MonthlyCashflowItem(
            year=k[0], month=k[1], income=v["income"], expenses=v["expenses"]
        )
        for k, v in cashflow_data.items()
    ]

    return CashflowStatistics(items=items)
