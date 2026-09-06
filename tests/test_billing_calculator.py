import pytest
from src.billing.calculator import BillingCalculator


def test_calculate_item_bill():
    calc = BillingCalculator()
    # 4 pieces of String Hoppers at Rs. 25.00 each = Rs. 100.00
    item = calc.calculate_item_bill(
        food_name="string_hoppers",
        display_name="String Hoppers",
        quantity=4,
        unit_price=25.00,
        serving_type="piece"
    )

    assert item.food_name == "string_hoppers"
    assert item.quantity == 4
    assert item.unit_price == 25.00
    assert item.total_price == 100.00
    assert "100.00" in item.formatted_total_price


def test_aggregate_bill():
    calc = BillingCalculator()
    item1 = calc.calculate_item_bill("string_hoppers", "String Hoppers", 4, 25.00)
    item2 = calc.calculate_item_bill("uludu_vade", "Uludu Vade", 1, 60.00)

    bill = calc.aggregate_bill([item1, item2])
    assert bill.item_count == 5
    assert bill.subtotal == 160.00
    assert bill.total_amount == 160.00
    assert "160.00" in bill.formatted_total


def test_aggregate_bill_with_discount():
    calc = BillingCalculator()
    item = calc.calculate_item_bill("noodles", "Fried Noodles", 2, 200.00)
    bill = calc.aggregate_bill([item], discount=50.00)
    assert bill.subtotal == 400.00
    assert bill.discount == 50.00
    assert bill.total_amount == 350.00
