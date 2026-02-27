import csv
import io
import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, and_, func, case, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from piggy.core.i18n import _
from piggy.models.database.account import Account
from piggy.models.database.category import Category
from piggy.models.database.transaction import Transaction, TransactionType


async def export_transactions_csv(
    db: AsyncSession,
    user_id: uuid.UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> str:
    """Export transactions as a CSV string."""
    query = (
        select(Transaction)
        .join(Account, Transaction.account_id == Account.id)
        .options(joinedload(Transaction.category), joinedload(Transaction.account))
        .where(Account.user_id == user_id)
        .order_by(Transaction.timestamp.desc())
    )

    if start_date:
        query = query.where(Transaction.timestamp >= start_date)
    if end_date:
        query = query.where(Transaction.timestamp <= end_date)

    result = await db.execute(query)
    transactions = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["Date", "Description", "Amount", "Type", "Category", "Account"])

    for tx in transactions:
        writer.writerow(
            [
                tx.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                tx.description,
                f"{tx.amount:.2f}",
                tx.type.value,
                tx.category.name if tx.category else "Uncategorized",
                tx.account.name,
            ]
        )

    return output.getvalue()


async def generate_monthly_pdf_report(
    db: AsyncSession, user_id: uuid.UUID, year: int, month: int
) -> bytes:
    """Generate an expanded PDF report for a specific month for the given user."""
    from fpdf import FPDF  # type: ignore
    from dateutil.relativedelta import relativedelta
    from piggy.models.database.budget import Budget
    from piggy.models.database.recurring_payment import RecurringPayment

    # Compute date range
    start_date = date(year, month, 1)
    end_date = start_date + relativedelta(months=1)

    # 1. Aggregate totals (Income vs Expenses)
    totals_query = (
        select(
            func.sum(
                case(
                    (Transaction.type == TransactionType.INCOME, Transaction.amount),
                    else_=0,
                )
            ).label("income"),
            func.sum(
                case(
                    (Transaction.type == TransactionType.EXPENSE, Transaction.amount),
                    else_=0,
                )
            ).label("expenses"),
        )
        .join(Account, Transaction.account_id == Account.id)
        .where(
            and_(
                Account.user_id == user_id,
                Transaction.timestamp >= start_date,
                Transaction.timestamp < end_date,
                Transaction.type.in_([TransactionType.INCOME, TransactionType.EXPENSE]),
            )
        )
    )
    res = await db.execute(totals_query)
    row = res.one_or_none()
    income = Decimal(row.income or 0) if row else Decimal(0)
    expenses = Decimal(row.expenses or 0) if row else Decimal(0)

    # 2. Top categories by spend
    cat_query = (
        select(Category.name, func.sum(Transaction.amount).label("spent"))
        .join(Account, Transaction.account_id == Account.id)
        .where(
            and_(
                Account.user_id == user_id,
                Transaction.timestamp >= start_date,
                Transaction.timestamp < end_date,
                Transaction.type == TransactionType.EXPENSE,
                Transaction.category_id.is_not(None),
            )
        )
        .group_by(Category.name)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(5)
    )
    top_cats = list((await db.execute(cat_query)).all())

    # 3. Budget vs Actual
    # Use a subquery to avoid cartesian products and correctly filter by user
    actual_spent_subquery = (
        select(
            Transaction.category_id,
            func.sum(Transaction.amount).label("total_spent")
        )
        .join(Account, Transaction.account_id == Account.id)
        .where(
            and_(
                Account.user_id == user_id,
                Transaction.timestamp >= start_date,
                Transaction.timestamp < end_date,
                Transaction.type == TransactionType.EXPENSE,
            )
        )
        .group_by(Transaction.category_id)
        .subquery()
    )

    budget_query = (
        select(
            Category.name,
            Budget.amount.label("budget"),
            func.coalesce(actual_spent_subquery.c.total_spent, 0).label("actual"),
        )
        .join(Category, Budget.category_id == Category.id)
        .outerjoin(
            actual_spent_subquery,
            actual_spent_subquery.c.category_id == Category.id
        )
        .where(Budget.user_id == user_id)
    )
    budgets_res = list((await db.execute(budget_query)).all())

    # 4. Largest single transactions
    large_tx_query = (
        select(Transaction.timestamp, Transaction.description, Transaction.amount)
        .join(Account, Transaction.account_id == Account.id)
        .where(
            and_(
                Account.user_id == user_id,
                Transaction.timestamp >= start_date,
                Transaction.timestamp < end_date,
                Transaction.type == TransactionType.EXPENSE,
            )
        )
        .order_by(Transaction.amount.desc())
        .limit(5)
    )
    large_txs = list((await db.execute(large_tx_query)).all())

    # 5. Subscriptions (Active Recurring Payments)
    recurring_query = select(
        RecurringPayment.name, RecurringPayment.amount, RecurringPayment.interval
    ).where(
        and_(
            RecurringPayment.user_id == user_id,
            RecurringPayment.is_subscription.is_(True),
        )
    )
    subscriptions = list((await db.execute(recurring_query)).all())

    # Build PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Theme Colors (based on email.html)
    # Background Blue: #E3F2FD (227, 242, 253)
    # Primary Blue: #7DB9E8 (125, 185, 232)
    # Text Gray: #4A4A4A (74, 74, 74)

    # Header with Branding
    pdf.set_fill_color(125, 185, 232)  # Primary Blue
    pdf.rect(0, 0, 210, 40, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 20, "piggy", ln=True, align="C")
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"{_('report.title')} - {year}-{month:02d}", ln=True, align="C")
    pdf.ln(15)

    pdf.set_text_color(74, 74, 74)  # Reset to Text Gray

    # 1. Summary Section
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _("report.summary"), ln=True)
    pdf.set_draw_color(125, 185, 232)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 12)
    pdf.cell(100, 8, f"{_('report.income')}:", 0)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(0, 150, 0)  # Green for income
    pdf.cell(0, 8, f"+ {income:,.2f} EUR", ln=True, align="R")

    pdf.set_text_color(74, 74, 74)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(100, 8, f"{_('report.expenses')}:", 0)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(200, 0, 0)  # Red for expenses
    pdf.cell(0, 8, f"- {expenses:,.2f} EUR", ln=True, align="R")

    pdf.set_text_color(74, 74, 74)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(100, 10, f"{_('report.net')}:", 0)
    net = income - expenses
    if net >= 0:
        pdf.set_text_color(0, 150, 0)
        prefix = "+"
    else:
        prefix = ""
        pdf.set_text_color(200, 0, 0)
    pdf.cell(0, 10, f"{prefix}{net:,.2f} EUR", ln=True, align="R")
    pdf.set_text_color(74, 74, 74)
    pdf.ln(5)

    # 2. Budget vs Actual
    if budgets_res:
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, _("report.budget_control"), ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(80, 8, _("report.category"), 1)
        pdf.cell(40, 8, _("report.budget"), 1, 0, "C")
        pdf.cell(40, 8, _("report.actual"), 1, 0, "C")
        pdf.cell(30, 8, _("report.status"), 1, 1, "C")

        pdf.set_font("Helvetica", "", 10)
        for b_name, b_amount, b_actual in budgets_res:
            pdf.cell(80, 8, b_name, 1)
            pdf.cell(40, 8, f"{b_amount:,.2f} EUR", 1, 0, "R")
            pdf.cell(40, 8, f"{b_actual:,.2f} EUR", 1, 0, "R")
            if b_actual > b_amount:
                pdf.set_text_color(200, 0, 0)
                status_txt = _("report.over_budget")
            else:
                pdf.set_text_color(0, 120, 0)
                status_txt = _("report.budget_ok")
            pdf.cell(30, 8, status_txt, 1, 1, "C")
            pdf.set_text_color(74, 74, 74)
        pdf.ln(10)

    # 3. Largest single transactions
    if large_txs:
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, _("report.largest_expenses"), ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(30, 8, _("report.date"), 1)
        pdf.cell(120, 8, _("report.description"), 1)
        pdf.cell(40, 8, _("report.amount"), 1, 1, "C")

        pdf.set_font("Helvetica", "", 10)
        for t_date, t_desc, t_amount in large_txs:
            pdf.cell(30, 8, t_date.strftime("%d.%m.%Y"), 1)
            pdf.cell(120, 8, (t_desc[:60] + "..") if len(t_desc) > 60 else t_desc, 1)
            pdf.cell(40, 8, f"{t_amount:,.2f} EUR", 1, 1, "R")
        pdf.ln(10)

    # 4. Subscriptions
    if subscriptions:
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, _("report.active_subscriptions"), ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(110, 8, _("report.name"), 1)
        pdf.cell(40, 8, _("report.interval"), 1)
        pdf.cell(40, 8, _("report.amount"), 1, 1, "C")

        pdf.set_font("Helvetica", "", 10)
        for s_name, s_amount, s_interval in subscriptions:
            pdf.cell(110, 8, s_name, 1)
            pdf.cell(40, 8, str(s_interval), 1)
            pdf.cell(40, 8, f"{s_amount:,.2f} EUR", 1, 1, "R")
        pdf.ln(10)

    # Footer with page numbers
    pdf.set_y(-15)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, f"{_('report.page')} {pdf.page_no()}", 0, 0, "C")

    # Return PDF as bytes
    return bytes(pdf.output())
