import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from database.connection import init_database
from database.seed.seed_runner import seed_database_if_empty
from src.transactions.service import TransactionService
from src.transactions.schemas import (
    TransactionCreateRequest,
    TransactionItemInput,
    PaymentMethod,
    PaymentStatus
)
from src.application.app import app


@pytest.fixture(autouse=True)
def setup_db():
    init_database()
    seed_database_if_empty()


def test_create_transaction_success():
    service = TransactionService()
    request = TransactionCreateRequest(
        employee_code="EMP001",
        items=[
            TransactionItemInput(food_name="rice_and_curry", quantity=1),
            TransactionItemInput(food_name="chicken_curry", quantity=1),
            TransactionItemInput(food_name="dhal_curry", quantity=1)
        ],
        payment_method=PaymentMethod.PAYROLL
    )
    tx = service.create_transaction(request)

    assert tx.id is not None
    assert tx.transaction_code.startswith("TX-")
    assert tx.employee_code == "EMP001"
    assert len(tx.items) == 3
    assert tx.total_amount > 0.0
    assert tx.total_calories > 0.0
    assert tx.total_protein > 0.0
    assert tx.payment_status == "completed"
    assert tx.payment_method == "payroll"


def test_create_transaction_unknown_employee_fails():
    service = TransactionService()
    request = TransactionCreateRequest(
        employee_code="EMP_NON_EXISTENT_9999",
        items=[TransactionItemInput(food_name="rice_and_curry", quantity=1)]
    )
    with pytest.raises(ValueError, match="not found"):
        service.create_transaction(request)


def test_get_single_transaction_by_id_and_code():
    service = TransactionService()
    request = TransactionCreateRequest(
        employee_code="EMP002",
        items=[TransactionItemInput(food_name="noodles", quantity=2)]
    )
    tx = service.create_transaction(request)

    by_id = service.get_transaction(str(tx.id))
    assert by_id is not None
    assert by_id.transaction_code == tx.transaction_code
    assert by_id.employee_code == "EMP002"

    by_code = service.get_transaction(tx.transaction_code)
    assert by_code is not None
    assert by_code.id == tx.id
    assert len(by_code.items) == 1
    assert by_code.items[0].quantity == 2


def test_employee_meal_history_and_summary():
    service = TransactionService()
    # Create 2 transactions for EMP003
    service.create_transaction(TransactionCreateRequest(
        employee_code="EMP003",
        items=[TransactionItemInput(food_name="string_hoppers", quantity=1)]
    ))
    service.create_transaction(TransactionCreateRequest(
        employee_code="EMP003",
        items=[TransactionItemInput(food_name="hoppers", quantity=2)]
    ))

    history = service.get_employee_meal_history("EMP003")
    assert history.employee_code == "EMP003"
    assert history.total_meals >= 2
    assert history.total_calories > 0.0
    assert history.total_spent_lkr > 0.0
    assert len(history.meals) >= 2

    # Monthly summary
    summary = service.get_employee_monthly_summary("EMP003")
    assert summary.employee_code == "EMP003"
    assert summary.total_meals >= 2
    assert summary.avg_meal_cost > 0.0
    assert "protein_pct" in summary.macro_distribution_pct


def test_historical_price_preservation_rule():
    """
    Rule 1 Verification:
    Updating a food price in the future MUST NOT alter historical transaction totals or item prices.
    """
    from src.billing.schemas import PriceUpdate
    service = TransactionService()
    food = service.food_service.get_food("chicken_curry")

    # Set baseline price (Rs. 150.00)
    service.billing_service.update_price(food["id"], PriceUpdate(price=150.00))

    # Create transaction with baseline price
    tx = service.create_transaction(TransactionCreateRequest(
        employee_code="EMP001",
        items=[TransactionItemInput(food_name="chicken_curry", quantity=1)]
    ))
    original_item_price = tx.items[0].unit_price
    original_total_amount = tx.total_amount
    assert original_item_price == 150.00

    # Admin changes chicken curry price to Rs. 350.00
    service.billing_service.update_price(food["id"], PriceUpdate(price=350.00))

    # Retrieve past transaction
    past_tx = service.get_transaction(str(tx.id))
    assert past_tx.items[0].unit_price == original_item_price
    assert past_tx.total_amount == original_total_amount
    assert past_tx.items[0].unit_price == 150.00
    assert past_tx.items[0].unit_price != 350.00


def test_transaction_api_endpoints():
    client = TestClient(app)

    # 1. Create transaction via API
    payload = {
        "employee_code": "EMP001",
        "items": [
            {"food_name": "rice_and_curry", "quantity": 1},
            {"food_name": "dhal_curry", "quantity": 1}
        ],
        "payment_method": "payroll"
    }
    res = client.post("/api/v1/meal-transactions", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is True
    tx_code = data["transaction"]["transaction_code"]

    # 2. Get single transaction
    get_res = client.get(f"/api/v1/meal-transactions/{tx_code}")
    assert get_res.status_code == 200
    assert get_res.json()["transaction"]["transaction_code"] == tx_code

    # 3. Get employee meal history
    hist_res = client.get("/api/v1/employees/EMP001/meal-history")
    assert hist_res.status_code == 200
    assert hist_res.json()["data"]["total_meals"] >= 1

    # 4. Get employee monthly summary
    sum_res = client.get("/api/v1/employees/EMP001/meal-history/summary")
    assert sum_res.status_code == 200
    assert sum_res.json()["data"]["total_meals"] >= 1

    # 5. Admin list transactions with filter
    list_res = client.get("/api/v1/meal-transactions?employee_id=1")
    assert list_res.status_code == 200
    assert list_res.json()["count"] >= 1

    # 6. Canteen analytics summary
    ana_res = client.get("/api/v1/analytics/canteen-summary")
    assert ana_res.status_code == 200
    assert ana_res.json()["analytics"]["total_transactions"] >= 1
