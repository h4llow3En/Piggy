"""
v1 API routes.
"""

from fastapi import APIRouter

from piggy.api.v1 import (
    accounts,
    users,
    transactions,
    categories,
    recurring_payments,
    dashboard,
    budgets,
    statistic,
    bank,
    exports,
)

api_v1_router = APIRouter(prefix="/v1")

# transactions router has no prefix because it shares
# the same prefix as accounts but is more specific
api_v1_router.include_router(transactions.router, tags=["transactions"])
api_v1_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_v1_router.include_router(users.router, prefix="/users", tags=["users"])

# budgets router has no prefix because it shares
# the same prefix as categories but is more specific
api_v1_router.include_router(budgets.router, tags=["budgets"])

api_v1_router.include_router(
    categories.router, prefix="/categories", tags=["categories"]
)
api_v1_router.include_router(
    recurring_payments.router, prefix="/recurring-payments", tags=["recurring-payments"]
)
api_v1_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_v1_router.include_router(statistic.router, prefix="/statistic", tags=["statistic"])

api_v1_router.include_router(exports.router, prefix="/exports", tags=["exports"])

api_v1_router.include_router(bank.router, prefix="/bank", tags=["bank"])
