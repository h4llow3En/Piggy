import contextlib
import signal
import pytest
from datetime import date

from piggy.core.utils import get_next_recurring_payment_occurrence
from piggy.models.database.recurring_payment import RecurringInterval


@contextlib.contextmanager
def time_limit(seconds: int):
    """
    Abort after `seconds`, via SIGALRM rather than asyncio.

    A non-terminating interval spins in a synchronous while loop and blocks the
    event loop itself, so asyncio.wait_for would never get a chance to fire.
    """

    def _raise(*_):
        raise TimeoutError("call did not terminate")

    previous = signal.signal(signal.SIGALRM, _raise)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


@pytest.mark.skipif(not hasattr(signal, "SIGALRM"), reason="requires POSIX signals")
@pytest.mark.parametrize("interval", list(RecurringInterval))
def test_next_occurrence_terminates_for_every_interval(interval):
    """Quarterly and Semi-Annually had no case and looped forever."""
    with time_limit(5):
        result = get_next_recurring_payment_occurrence(
            date(2024, 1, 1), interval, 30, date(2026, 7, 26)
        )
    assert result >= date(2026, 7, 26)


@pytest.mark.asyncio
async def test_dashboard_summary_with_quarterly_payment(auth_client):
    """End to end guard: a Quarterly payment used to hang /dashboard/summary."""
    today = date.today()
    await auth_client.post(
        "/api/v1/recurring-payments/",
        json={
            "name": "Quarterly Insurance",
            "amount": 120.0,
            "type": "Expense",
            "interval": "Quarterly",
            "start_date": date(today.year - 1, 1, 1).isoformat(),
        },
    )

    with time_limit(10):
        response = await auth_client.get(
            f"/api/v1/dashboard/summary?month={today.month}&year={today.year}"
        )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_create_recurring_payment(auth_client):
    response = await auth_client.post(
        "/api/v1/recurring-payments/",
        json={
            "name": "Netflix",
            "amount": 17.99,
            "type": "Expense",
            "interval": "Monthly",
            "start_date": date.today().isoformat(),
            "is_subscription": True
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Netflix"
    assert float(data["amount"]) == 17.99

@pytest.mark.asyncio
async def test_read_recurring_payments(auth_client):
    await auth_client.post(
        "/api/v1/recurring-payments/",
        json={
            "name": "Internet",
            "amount": 40.0,
            "type": "Expense",
            "interval": "Monthly",
            "start_date": date.today().isoformat()
        },
    )
    
    response = await auth_client.get("/api/v1/recurring-payments/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Internet"

@pytest.mark.asyncio
async def test_update_recurring_payment(auth_client):
    create_resp = await auth_client.post(
        "/api/v1/recurring-payments/",
        json={
            "name": "Gym",
            "amount": 30.0,
            "type": "Expense",
            "interval": "Monthly",
            "start_date": date.today().isoformat()
        },
    )
    payment_id = create_resp.json()["id"]
    
    response = await auth_client.put(
        f"/api/v1/recurring-payments/{payment_id}",
        json={"amount": 35.0},
    )
    assert response.status_code == 200
    assert float(response.json()["amount"]) == 35.0

@pytest.mark.asyncio
async def test_delete_recurring_payment(auth_client):
    create_resp = await auth_client.post(
        "/api/v1/recurring-payments/",
        json={
            "name": "To Delete",
            "amount": 10.0,
            "type": "Expense",
            "interval": "Monthly",
            "start_date": date.today().isoformat()
        },
    )
    payment_id = create_resp.json()["id"]
    
    response = await auth_client.delete(f"/api/v1/recurring-payments/{payment_id}")
    assert response.status_code == 204
    
    get_resp = await auth_client.get(f"/api/v1/recurring-payments/{payment_id}")
    assert get_resp.status_code == 404
