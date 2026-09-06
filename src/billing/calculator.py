from typing import List
from src.billing.schemas import BillingItem, BillingCalculationResult


class BillingCalculator:
    """
    Mathematical billing calculator with currency formatting.
    """

    @staticmethod
    def format_currency(amount: float, currency_symbol: str = "Rs. ") -> str:
        """Formats amount with 2 decimal places and currency symbol."""
        return f"{currency_symbol}{amount:,.2f}"

    @classmethod
    def calculate_item_bill(
        cls,
        food_name: str,
        display_name: str,
        quantity: int,
        unit_price: float,
        serving_type: str = "piece"
    ) -> BillingItem:
        """
        Calculates item total = unit_price * quantity.
        """
        unit_price_clean = max(0.0, float(unit_price))
        total_price = round(unit_price_clean * quantity, 2)

        return BillingItem(
            food_name=food_name,
            display_name=display_name,
            quantity=quantity,
            serving_type=serving_type,
            unit_price=unit_price_clean,
            total_price=total_price,
            formatted_unit_price=cls.format_currency(unit_price_clean),
            formatted_total_price=cls.format_currency(total_price)
        )

    @classmethod
    def aggregate_bill(
        cls,
        items: List[BillingItem],
        discount: float = 0.0,
        tax: float = 0.0
    ) -> BillingCalculationResult:
        """
        Aggregates items into a grand total bill.
        """
        subtotal = round(sum(item.total_price for item in items), 2)
        discount_amount = max(0.0, round(float(discount), 2))
        tax_amount = max(0.0, round(float(tax), 2))
        total_amount = max(0.0, round(subtotal - discount_amount + tax_amount, 2))
        item_count = sum(item.quantity for item in items)

        return BillingCalculationResult(
            items=items,
            item_count=item_count,
            subtotal=subtotal,
            discount=discount_amount,
            tax=tax_amount,
            total_amount=total_amount,
            currency="LKR",
            formatted_total=cls.format_currency(total_amount)
        )
