from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import uuid

from src.transactions.schemas import (
    TransactionItemInput,
    TransactionCreateRequest,
    TransactionItemResponse,
    TransactionResponse,
    MealHistoryItem,
    EmployeeMealHistoryResponse,
    MonthlySummaryResponse,
    CanteenAnalyticsSummary
)
from src.transactions.repository import TransactionRepository
from src.foods.service import FoodService
from src.nutrition.service import NutritionService
from src.billing.service import BillingService
from src.profiles.employee_service import EmployeeService
from src.utils.logging import app_logger


class TransactionService:
    """
    Business Service Layer for Phase 5 Meal Transactions & Meal History.
    Integrates Phase 1, Phase 2, Phase 3, and Phase 4 subsystems.
    Guarantees server-side computation and permanent historical snapshotting.
    """

    def __init__(
        self,
        repository: Optional[TransactionRepository] = None,
        food_service: Optional[FoodService] = None,
        nutrition_service: Optional[NutritionService] = None,
        billing_service: Optional[BillingService] = None,
        employee_service: Optional[EmployeeService] = None,
        db_path: Optional[Path] = None
    ):
        self.repository = repository or TransactionRepository(db_path=db_path)
        self.food_service = food_service or FoodService(db_path=db_path)
        self.nutrition_service = nutrition_service or NutritionService(db_path=db_path)
        self.billing_service = billing_service or BillingService(db_path=db_path)
        self.employee_service = employee_service or EmployeeService(db_path=db_path)

    def _generate_transaction_code(self) -> str:
        """Generates a human-friendly unique transaction identifier (e.g. TX-20260905-A1B2)."""
        today_str = datetime.now().strftime("%Y%m%d")
        short_id = uuid.uuid4().hex[:5].upper()
        return f"TX-{today_str}-{short_id}"

    def create_transaction(self, request: TransactionCreateRequest) -> TransactionResponse:
        """
        Creates a new immutable meal transaction.
        Calculates all prices, quantities, and nutrients strictly on the backend.
        """
        # Step 1: Validate and retrieve Employee
        emp = None
        if request.employee_id:
            emp = self.employee_service.get_employee(str(request.employee_id))
        elif request.employee_code:
            emp = self.employee_service.get_employee(request.employee_code)

        if not emp:
            target = request.employee_code or request.employee_id
            raise ValueError(f"Employee '{target}' not found or inactive in the canteen registry.")

        employee_id = emp["id"]

        # Step 2: Compute Itemized Snapshots (Nutrition + Billing)
        item_snapshots: List[Dict[str, Any]] = []
        total_calories = 0.0
        total_protein = 0.0
        total_carbs = 0.0
        total_fat = 0.0
        total_sugar = 0.0
        total_fiber = 0.0
        total_sodium_mg = 0.0
        total_amount = 0.0

        for item_in in request.items:
            # Find food entity
            food = None
            if item_in.food_name:
                food = self.food_service.get_food(item_in.food_name)
            elif item_in.food_id:
                food = self.food_service.get_food(str(item_in.food_id))

            qty = max(item_in.quantity, 1)

            if food:
                fid = food["id"]
                cname = food["class_name"]
                dname = food["display_name"]
                stype = food["serving_type"]
                std_weight = float(food.get("standard_serving_g") or 100.0)
                actual_weight = item_in.portion_size_g or (std_weight * qty)

                # Get price snapshot
                price_rec = self.billing_service.billing_repo.get_current_price_by_food_id(fid)
                unit_price = float(price_rec["price"]) if price_rec else 0.0
                subtotal = round(unit_price * qty, 2)

                # Get scaled nutrition snapshot
                nutr_calc = self.nutrition_service.calculate_single(food_name=cname, quantity=qty)
                if nutr_calc:
                    cals = float(nutr_calc.calories_kcal)
                    prot = float(nutr_calc.protein_g)
                    carb = float(nutr_calc.carbs_g)
                    fat = float(nutr_calc.fat_g)
                    sug = float(nutr_calc.sugar_g)
                    fib = float(nutr_calc.fiber_g)
                    sod = float(nutr_calc.sodium_mg)
                else:
                    cals = prot = carb = fat = sug = fib = sod = 0.0
            else:
                # Fallback for unrecognized items
                cname = item_in.food_name or f"item_{item_in.food_id}"
                dname = cname.replace("_", " ").title()
                unit_price = 0.0
                subtotal = 0.0
                actual_weight = 100.0 * qty
                cals = prot = carb = fat = sug = fib = sod = 0.0
                fid = None

            item_snapshots.append({
                "food_id": fid,
                "food_name": cname,
                "display_name": dname,
                "quantity": qty,
                "serving_size_g": actual_weight,
                "calories": round(cals, 1),
                "protein": round(prot, 1),
                "carbs": round(carb, 1),
                "fat": round(fat, 1),
                "sugar": round(sug, 1),
                "fiber": round(fib, 1),
                "sodium_mg": round(sod, 1),
                "unit_price": unit_price,
                "subtotal": subtotal
            })

            total_calories += cals
            total_protein += prot
            total_carbs += carb
            total_fat += fat
            total_sugar += sug
            total_fiber += fib
            total_sodium_mg += sod
            total_amount += subtotal

        # Step 3: Insert Transaction record into database
        tx_code = self._generate_transaction_code()
        tx_data = {
            "transaction_code": tx_code,
            "employee_id": employee_id,
            "total_calories": round(total_calories, 1),
            "total_protein": round(total_protein, 1),
            "total_carbs": round(total_carbs, 1),
            "total_fat": round(total_fat, 1),
            "total_sugar": round(total_sugar, 1),
            "total_fiber": round(total_fiber, 1),
            "total_sodium_mg": round(total_sodium_mg, 1),
            "total_amount": round(total_amount, 2),
            "payment_status": request.payment_status.value,
            "payment_method": request.payment_method.value,
            "transaction_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        tx_id = self.repository.create_transaction(tx_data, item_snapshots)
        app_logger.info(f"Created meal transaction {tx_code} (ID: {tx_id}) for {emp['employee_code']} — Rs. {total_amount:.2f}")

        # Step 4: Return full transaction response
        return self.get_transaction(str(tx_id))

    def get_transaction(self, id_or_code: str) -> Optional[TransactionResponse]:
        """Retrieves full transaction entity by numeric ID or transaction code."""
        raw = None
        if id_or_code.isdigit():
            raw = self.repository.get_transaction_by_id(int(id_or_code))
        if not raw:
            raw = self.repository.get_transaction_by_code(id_or_code)
        if not raw:
            return None

        emp_name = f"{raw.get('first_name', '')} {raw.get('last_name', '')}".strip() or raw.get("employee_code", "Staff")
        total_amt = float(raw["total_amount"])

        items = [
            TransactionItemResponse(
                id=item["id"],
                transaction_id=item["transaction_id"],
                food_id=item.get("food_id"),
                food_name=item["food_name"],
                display_name=item["display_name"],
                quantity=item["quantity"],
                serving_size_g=item["serving_size_g"],
                calories=item["calories"],
                protein=item["protein"],
                carbs=item["carbs"],
                fat=item["fat"],
                sugar=item.get("sugar", 0.0),
                fiber=item.get("fiber", 0.0),
                sodium_mg=item.get("sodium_mg", 0.0),
                unit_price=item["unit_price"],
                subtotal=item["subtotal"]
            )
            for item in raw.get("items", [])
        ]

        return TransactionResponse(
            id=raw["id"],
            transaction_code=raw["transaction_code"],
            employee_id=raw["employee_id"],
            employee_code=raw["employee_code"],
            employee_name=emp_name,
            department=raw.get("department") or "General",
            total_calories=float(raw["total_calories"]),
            total_protein=float(raw["total_protein"]),
            total_carbs=float(raw["total_carbs"]),
            total_fat=float(raw["total_fat"]),
            total_sugar=float(raw.get("total_sugar", 0.0)),
            total_fiber=float(raw.get("total_fiber", 0.0)),
            total_sodium_mg=float(raw.get("total_sodium_mg", 0.0)),
            total_amount=total_amt,
            formatted_total_amount=f"Rs. {total_amt:.2f}",
            payment_status=raw["payment_status"],
            payment_method=raw["payment_method"],
            transaction_date=str(raw["transaction_date"]),
            created_at=str(raw["created_at"]),
            items=items
        )

    def get_employee_meal_history(
        self,
        id_or_code: str,
        date_filter: Optional[str] = None,
        month_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> EmployeeMealHistoryResponse:
        """
        Retrieves formatted meal history for an employee.
        Groups food items and formats dates/times for frontend display.
        """
        emp = self.employee_service.get_employee(id_or_code)
        if not emp:
            raise ValueError(f"Employee '{id_or_code}' not found.")

        employee_id = emp["id"]
        raw_txs = self.repository.list_employee_transactions(
            employee_id=employee_id,
            date_filter=date_filter,
            month_filter=month_filter,
            limit=limit,
            offset=offset
        )

        meals: List[MealHistoryItem] = []
        total_cals = 0.0
        total_spent = 0.0

        for r in raw_txs:
            foods_list = [item["display_name"] for item in r.get("items", [])]
            t_amt = float(r["total_amount"])
            t_cal = float(r["total_calories"])
            total_cals += t_cal
            total_spent += t_amt

            # Parse date and time
            dt_str = str(r["transaction_date"])
            try:
                dt_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                date_fmt = dt_obj.strftime("%B %d, %Y")
                time_fmt = dt_obj.strftime("%I:%M %p")
            except Exception:
                date_fmt = dt_str.split(" ")[0] if " " in dt_str else dt_str
                time_fmt = dt_str.split(" ")[1] if " " in dt_str else ""

            meals.append(MealHistoryItem(
                transaction_id=r["id"],
                transaction_code=r["transaction_code"],
                foods=foods_list,
                items_detail=r.get("items", []),
                calories=t_cal,
                amount=t_amt,
                formatted_amount=f"Rs. {t_amt:.2f}",
                date=date_fmt,
                time=time_fmt,
                timestamp=dt_str,
                macros={
                    "protein_g": float(r["total_protein"]),
                    "carbs_g": float(r["total_carbs"]),
                    "fat_g": float(r["total_fat"])
                }
            ))

        emp_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip() or emp.get("employee_code", "Staff")

        return EmployeeMealHistoryResponse(
            employee_id=employee_id,
            employee_code=emp["employee_code"],
            employee_name=emp_name,
            department=emp.get("department") or "General",
            total_meals=len(meals),
            total_calories=round(total_cals, 1),
            total_spent_lkr=round(total_spent, 2),
            formatted_total_spent=f"Rs. {total_spent:.2f}",
            meals=meals
        )

    def get_employee_monthly_summary(
        self,
        id_or_code: str,
        month: Optional[str] = None
    ) -> MonthlySummaryResponse:
        """
        Calculates monthly summary statistics for an employee (useful for Phase 6 recommendations).
        """
        emp = self.employee_service.get_employee(id_or_code)
        if not emp:
            raise ValueError(f"Employee '{id_or_code}' not found.")

        target_month = month or datetime.now().strftime("%Y-%m")
        stats = self.repository.get_employee_monthly_stats(emp["id"], target_month)

        total_meals = int(stats["total_meals"])
        total_cals = float(stats["total_calories"])
        total_spent = float(stats["total_spent"])
        active_days = max(int(stats.get("active_days", 1)), 1)

        avg_daily_cal = round(total_cals / active_days, 1) if active_days > 0 else 0.0
        avg_meal_cost = round(total_spent / total_meals, 2) if total_meals > 0 else 0.0

        # Calculate macro energy percentages
        prot_g = float(stats.get("total_protein", 0.0))
        carb_g = float(stats.get("total_carbs", 0.0))
        fat_g = float(stats.get("total_fat", 0.0))
        total_macro_energy = (prot_g * 4) + (carb_g * 4) + (fat_g * 9)

        macro_pcts = {
            "protein_pct": round((prot_g * 4 / total_macro_energy) * 100, 1) if total_macro_energy > 0 else 0.0,
            "carbs_pct": round((carb_g * 4 / total_macro_energy) * 100, 1) if total_macro_energy > 0 else 0.0,
            "fat_pct": round((fat_g * 9 / total_macro_energy) * 100, 1) if total_macro_energy > 0 else 0.0
        }

        emp_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip() or emp.get("employee_code", "Staff")

        return MonthlySummaryResponse(
            employee_id=emp["id"],
            employee_code=emp["employee_code"],
            employee_name=emp_name,
            month=target_month,
            total_meals=total_meals,
            total_calories=round(total_cals, 1),
            total_spent=round(total_spent, 2),
            formatted_total_spent=f"Rs. {total_spent:.2f}",
            avg_daily_calories=avg_daily_cal,
            avg_meal_cost=avg_meal_cost,
            macro_distribution_pct=macro_pcts
        )

    def list_all_transactions(
        self,
        employee_id: Optional[int] = None,
        date_str: Optional[str] = None,
        department: Optional[str] = None,
        payment_status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TransactionResponse]:
        """Lists transactions across the canteen with filters for the Admin Portal."""
        raw_list = self.repository.list_all_transactions(
            employee_id=employee_id,
            date_str=date_str,
            department=department,
            payment_status=payment_status,
            limit=limit,
            offset=offset
        )
        results = []
        for raw in raw_list:
            emp_name = f"{raw.get('first_name', '')} {raw.get('last_name', '')}".strip() or raw.get("employee_code", "Staff")
            total_amt = float(raw["total_amount"])
            items = [
                TransactionItemResponse(
                    id=item["id"],
                    transaction_id=item["transaction_id"],
                    food_id=item.get("food_id"),
                    food_name=item["food_name"],
                    display_name=item["display_name"],
                    quantity=item["quantity"],
                    serving_size_g=item["serving_size_g"],
                    calories=item["calories"],
                    protein=item["protein"],
                    carbs=item["carbs"],
                    fat=item["fat"],
                    sugar=item.get("sugar", 0.0),
                    fiber=item.get("fiber", 0.0),
                    sodium_mg=item.get("sodium_mg", 0.0),
                    unit_price=item["unit_price"],
                    subtotal=item["subtotal"]
                )
                for item in raw.get("items", [])
            ]
            results.append(TransactionResponse(
                id=raw["id"],
                transaction_code=raw["transaction_code"],
                employee_id=raw["employee_id"],
                employee_code=raw["employee_code"],
                employee_name=emp_name,
                department=raw.get("department") or "General",
                total_calories=float(raw["total_calories"]),
                total_protein=float(raw["total_protein"]),
                total_carbs=float(raw["total_carbs"]),
                total_fat=float(raw["total_fat"]),
                total_sugar=float(raw.get("total_sugar", 0.0)),
                total_fiber=float(raw.get("total_fiber", 0.0)),
                total_sodium_mg=float(raw.get("total_sodium_mg", 0.0)),
                total_amount=total_amt,
                formatted_total_amount=f"Rs. {total_amt:.2f}",
                payment_status=raw["payment_status"],
                payment_method=raw["payment_method"],
                transaction_date=str(raw["transaction_date"]),
                created_at=str(raw["created_at"]),
                items=items
            ))
        return results

    def get_canteen_analytics(self) -> CanteenAnalyticsSummary:
        """Retrieves top-level analytics for the canteen management dashboard."""
        analytics = self.repository.get_canteen_analytics()
        tot_rev = analytics["total_revenue_lkr"]
        today_rev = analytics["today_revenue_lkr"]

        return CanteenAnalyticsSummary(
            total_transactions=analytics["total_transactions"],
            total_revenue_lkr=tot_rev,
            formatted_total_revenue=f"Rs. {tot_rev:.2f}",
            today_transactions=analytics["today_transactions"],
            today_revenue_lkr=today_rev,
            formatted_today_revenue=f"Rs. {today_rev:.2f}",
            total_calories_served=analytics["total_calories_served"],
            top_dishes=analytics.get("top_dishes", [])
        )
