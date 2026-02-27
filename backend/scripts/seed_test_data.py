import asyncio
import random
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from piggy.core.database import async_session
from piggy.models.database.account import Account
from piggy.models.database.category import Category
from piggy.models.database.transaction import Transaction, TransactionType


async def seed_data():
    async with async_session() as session:
        # Get all existing accounts
        result = await session.execute(select(Account))
        accounts = result.scalars().all()

        if not accounts:
            print(
                "No accounts found in the database. Please create some accounts first."
            )
            return

        # Get all existing categories
        result = await session.execute(select(Category))
        categories = result.scalars().all()

        if not categories:
            print(
                "No categories found in the database. Please create some categories first."
            )
            return

        months = [
            (2025, 8),
            (2025, 9),
            (2025, 10),
            (2025, 11),
            (2025, 12),
            (2026, 1),
            (2026, 2),
        ]

        total_transactions = 0

        for account in accounts:
            print(
                f"Generating transactions for account: {account.name} (ID: {account.id})"
            )
            for year, month in months:
                for i in range(100):
                    # Random day in the month
                    day = random.randint(1, 28)
                    hour = random.randint(0, 23)
                    minute = random.randint(0, 59)
                    timestamp = datetime(year, month, day, hour, minute)

                    # Random transaction type
                    # 10% Income, 60% Expense, 15% Internal Transfer, 15% External Transfer
                    rand = random.random()

                    tx_type = TransactionType.EXPENSE
                    category_id = random.choice(categories).id
                    target_account_id = None
                    description = f"Test Transaction {i+1} - {month:02d}/{year}"
                    amount = Decimal(str(random.uniform(5.0, 150.0))).quantize(
                        Decimal("0.01")
                    )

                    if rand < 0.02:
                        tx_type = TransactionType.INCOME
                        description = f"Income {i+1} - {month:02d}/{year}"
                        amount = Decimal(str(random.uniform(500.0, 3000.0))).quantize(
                            Decimal("0.01")
                        )
                        category_id = random.choice(categories).id
                    elif rand < 0.8:
                        tx_type = TransactionType.EXPENSE
                        description = f"Expense {i+1} - {month:02d}/{year}"
                        category_id = random.choice(categories).id
                    else:
                        tx_type = TransactionType.TRANSFER
                        other_accounts = [a for a in accounts if a.id != account.id]
                        if other_accounts:
                            other_account = random.choice(other_accounts)
                            target_account_id = other_account.id
                            description = f"Internal Transfer to {other_account.name}"
                            category_id = None  # Transfer often doesn't have a category
                        else:
                            # Fallback if only one account exists
                            tx_type = TransactionType.EXPENSE
                            description = f"Expense (Transfer Fallback) {i+1}"
                            category_id = random.choice(categories).id

                    new_tx = Transaction(
                        id=uuid.uuid4(),
                        account_id=account.id,
                        target_account_id=target_account_id,
                        category_id=category_id,
                        description=description,
                        amount=amount,
                        type=tx_type,
                        timestamp=timestamp,
                    )
                    session.add(new_tx)
                    total_transactions += 1

                # Commit every month per account to avoid huge transactions
                await session.commit()
                print(f"  Month {month:02d}/{year} completed.")

        print(f"Finished! Seeded {total_transactions} transactions.")


if __name__ == "__main__":
    asyncio.run(seed_data())
