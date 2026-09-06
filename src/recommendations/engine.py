from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import re

from src.recommendations.schemas import (
    ScannedFoodInput,
    RecommendationRequest,
    FoodRecommendationItem,
    MealCombo,
    PlateAddOnSuggestion,
    NutritionalBudgetStatus,
    PersonalizedRecommendationResponse
)
from src.foods.service import FoodService
from src.nutrition.service import NutritionService
from src.billing.service import BillingService
from src.profiles.employee_service import EmployeeService
from src.profiles.profile_service import ProfileService
from src.transactions.service import TransactionService
from src.utils.logging import app_logger


class RecommendationEngine:
    """
    Phase 6: Personalized Meal Recommendation Engine.
    Combines:
      1. User Profile (BMI, Health Goal, Dietary Type, Allergens)
      2. Meal History (Today's consumed calories and macros)
      3. Current Nutrition (Scanned plate nutritional breakdown & deficits)
      4. Available Foods (Active Sri Lankan canteen catalog & dynamic pricing)
    """

    def __init__(
        self,
        food_service: Optional[FoodService] = None,
        nutrition_service: Optional[NutritionService] = None,
        billing_service: Optional[BillingService] = None,
        employee_service: Optional[EmployeeService] = None,
        profile_service: Optional[ProfileService] = None,
        transaction_service: Optional[TransactionService] = None,
        db_path: Optional[Path] = None
    ):
        self.food_service = food_service or FoodService(db_path=db_path)
        self.nutrition_service = nutrition_service or NutritionService(db_path=db_path)
        self.billing_service = billing_service or BillingService(db_path=db_path)
        self.employee_service = employee_service or EmployeeService(db_path=db_path)
        self.profile_service = profile_service or ProfileService(db_path=db_path)
        self.transaction_service = transaction_service or TransactionService(db_path=db_path)

    def _get_dish_emoji(self, name: str) -> str:
        n = name.lower()
        if 'rice' in n: return '🍛'
        if 'chicken' in n or 'meat' in n: return '🍗'
        if 'fish' in n: return '🐟'
        if 'egg' in n: return '🥚'
        if 'dhal' in n or 'curry' in n: return '🥘'
        if 'sambol' in n or 'mallum' in n or 'salad' in n: return '🥗'
        if 'noodle' in n or 'kottu' in n: return '🍜'
        if 'hopper' in n or 'roti' in n or 'pittu' in n or 'kiribath' in n: return '🥞'
        if 'roll' in n or 'samosa' in n or 'vade' in n or 'pan' in n: return '🥟'
        if 'watalappam' in n or 'dessert' in n or 'yogurt' in n: return '🍮'
        return '🍽️'

    def _get_dish_category(self, name: str) -> str:
        n = name.lower()
        if any(w in n for w in ['rice', 'curry', 'dhal', 'sambol', 'mallum', 'fish', 'chicken', 'egg']):
            return 'Curries & Rice'
        if any(w in n for w in ['roll', 'samosa', 'vade', 'pan', 'pastry', 'cutlet']):
            return 'Short Eats & Bakery'
        if any(w in n for w in ['hopper', 'roti', 'pittu', 'kiribath', 'noodle', 'kottu']):
            return 'Main Dishes'
        return 'Desserts & Extras'

    def _is_vegetarian_food(self, name: str) -> bool:
        n = name.lower()
        non_veg = ['chicken', 'meat', 'beef', 'pork', 'mutton', 'fish', 'prawn', 'seafood', 'crab']
        return not any(w in n for w in non_veg)

    def _is_vegan_food(self, name: str) -> bool:
        n = name.lower()
        non_vegan = ['chicken', 'meat', 'beef', 'pork', 'mutton', 'fish', 'prawn', 'seafood', 'crab', 'egg', 'milk', 'curd', 'cheese', 'butter', 'ghee']
        return not any(w in n for w in non_vegan)

    def _get_available_food_items(self) -> List[FoodRecommendationItem]:
        """Fetches all active food catalog items with price and nutrition snapshots."""
        raw_foods = self.food_service.list_foods(active_only=True)
        items: List[FoodRecommendationItem] = []

        for f in raw_foods:
            fid = f["id"]
            cname = f["class_name"]
            dname = f["display_name"]
            stype = f.get("serving_type") or "serving"
            std_weight = float(f.get("standard_serving_g") or 100.0)

            # Price
            price_rec = self.billing_service.billing_repo.get_current_price_by_food_id(fid)
            unit_price = float(price_rec["price"]) if price_rec else 150.0

            # Nutrition
            nutr = self.nutrition_service.nutrition_repo.get_by_food_id(fid)
            cal = float(nutr.get("calories_kcal") or 0.0) if nutr else 0.0
            prot = float(nutr.get("protein_g") or 0.0) if nutr else 0.0
            carbs = float(nutr.get("carbs_g") or 0.0) if nutr else 0.0
            fat = float(nutr.get("fat_g") or 0.0) if nutr else 0.0
            fiber = float(nutr.get("fiber_g") or 0.0) if nutr else 0.0

            # If basis is per_100g, scale to standard serving weight
            basis_type = nutr.get("basis_type", "per_unit") if nutr else "per_unit"
            if basis_type == "per_100g":
                ratio = std_weight / 100.0
                cal *= ratio
                prot *= ratio
                carbs *= ratio
                fat *= ratio
                fiber *= ratio

            items.append(FoodRecommendationItem(
                id=fid,
                food_name=cname,
                display_name=dname,
                price_lkr=unit_price,
                portion_size=f"1 {stype} ({std_weight:.0f}g)",
                calories_kcal=round(cal, 1),
                protein_g=round(prot, 1),
                carbs_g=round(carbs, 1),
                fat_g=round(fat, 1),
                fiber_g=round(fiber, 1),
                category=self._get_dish_category(dname or cname),
                emoji=self._get_dish_emoji(dname or cname),
                reason=None
            ))

        return items

    def _filter_safe_foods(
        self,
        foods: List[FoodRecommendationItem],
        diet_type: str,
        restrictions: List[str]
    ) -> List[FoodRecommendationItem]:
        """Filters out foods that violate dietary preferences or allergens."""
        safe_list: List[FoodRecommendationItem] = []
        diet = (diet_type or "normal").lower()
        lower_restrictions = [r.lower() for r in restrictions]

        for item in foods:
            name = (item.display_name or item.food_name).lower()

            # Diet type filtering
            if diet == 'vegetarian' and not self._is_vegetarian_food(name):
                continue
            if diet == 'vegan' and not self._is_vegan_food(name):
                continue
            if diet == 'diabetic' and item.calories_kcal > 450 and item.carbs_g > 65:
                continue

            # Allergens & restrictions filtering
            violates = False
            for r in lower_restrictions:
                if 'peanut' in r and 'peanut' in name:
                    violates = True; break
                if 'beef' in r and ('beef' in name or 'meat' in name):
                    violates = True; break
                if 'pork' in r and 'pork' in name:
                    violates = True; break
                if 'seafood' in r and any(s in name for s in ['fish', 'prawn', 'crab', 'seafood']):
                    violates = True; break
                if 'egg' in r and 'egg' in name:
                    violates = True; break

            if not violates:
                safe_list.append(item)

        return safe_list if safe_list else foods

    def get_personalized_recommendations(
        self,
        employee_code: str,
        scanned_items: Optional[List[Dict[str, Any]]] = None,
        time_of_day: str = "lunch"
    ) -> PersonalizedRecommendationResponse:
        """
        Main Phase 6 Inference Pipeline:
        1. Fetch Employee Profile
        2. Calculate Today's Consumed Calories from Meal History
        3. Determine Remaining Allowance & Deficits
        4. Curate Personalized Combos and Smart Plate Add-ons
        """
        # 1. Fetch Employee Core
        emp = self.employee_service.get_employee(employee_code)
        if not emp:
            raise ValueError(f"Employee code '{employee_code}' not found.")

        emp_id = emp["id"]
        f_name = emp.get('first_name', '') or ''
        l_name = emp.get('last_name', '') or ''
        full_name = f"{f_name} {l_name}".strip()
        emp_name = emp.get("name") or full_name or "Staff Member"
        department = emp.get("department") or "Engineering"

        # 2. Fetch User Profile
        prof = self.profile_service.get_profile(emp_id)
        if prof is not None:
            height_cm = float(getattr(prof, "height_cm", 175.0) or 175.0)
            weight_kg = float(getattr(prof, "weight_kg", 70.0) or 70.0)
            height_m = height_cm / 100.0
            bmi_val = getattr(prof, "bmi", None)
            bmi = round(float(bmi_val), 1) if bmi_val else (round(weight_kg / (height_m * height_m), 1) if height_m > 0 else 22.9)
            bmi_cat = getattr(prof, "bmi_category", "Normal weight")
            daily_target = float(getattr(prof, "daily_calorie_target", 2200.0) or 2200.0)
            
            raw_goal = getattr(prof, "health_goal", "maintain")
            health_goal = raw_goal.value if hasattr(raw_goal, "value") else str(raw_goal or "maintain")
            
            raw_diet = getattr(prof, "diet_type", "normal")
            diet_type = raw_diet.value if hasattr(raw_diet, "value") else str(raw_diet or "normal")
            
            notes = getattr(prof, "notes", "") or ""
            restrictions = [notes] if notes else []
        else:
            height_m = 1.75
            weight_kg = 70.0
            bmi = 22.9
            bmi_cat = "Normal weight"
            daily_target = 2200.0
            health_goal = "maintain"
            diet_type = "normal"
            restrictions = []

        # 3. Calculate Today's Meal History
        today_str = datetime.now().strftime("%Y-%m-%d")
        all_txs = self.transaction_service.repository.list_employee_transactions(emp_id, date_filter=today_str)
        today_consumed_cals = 0.0
        today_consumed_protein = 0.0
        today_consumed_carbs = 0.0

        for tx in all_txs:
            today_consumed_cals += float(tx.get("total_calories") or 0.0)
            today_consumed_protein += float(tx.get("total_protein") or 0.0)
            today_consumed_carbs += float(tx.get("total_carbs") or 0.0)

        remaining_cals = max(daily_target - today_consumed_cals, 0.0)

        # 4. Fetch Available Foods & Filter for Safety
        all_foods = self._get_available_food_items()
        safe_foods = self._filter_safe_foods(all_foods, diet_type, restrictions)

        # Index safe foods by class_name & id for rapid lookup
        foods_by_name = {f.food_name.lower(): f for f in safe_foods}
        foods_by_id = {f.id: f for f in safe_foods}

        # 5. Evaluate Scanned Plate (if provided)
        current_plate_cals = 0.0
        current_plate_prot = 0.0
        current_plate_carbs = 0.0
        current_plate_fiber = 0.0
        warnings: List[str] = []
        smart_add_ons: List[PlateAddOnSuggestion] = []

        if scanned_items and len(scanned_items) > 0:
            for sc in scanned_items:
                s_name = sc.get("food_name", "").lower()
                s_qty = int(sc.get("quantity", 1))

                # Check allergen/diet violation in scanned plate!
                if diet_type == 'vegetarian' and not self._is_vegetarian_food(s_name):
                    warnings.append(f"⚠️ Dietary Conflict: '{s_name}' contains non-vegetarian ingredients.")
                if diet_type == 'vegan' and not self._is_vegan_food(s_name):
                    warnings.append(f"⚠️ Dietary Conflict: '{s_name}' contains animal/dairy products.")

                for r in restrictions:
                    if 'peanut' in r.lower() and 'peanut' in s_name:
                        warnings.append(f"🚨 ALLERGEN ALERT: '{s_name}' contains peanuts!")
                    if 'beef' in r.lower() and ('beef' in s_name or 'meat' in s_name):
                        warnings.append(f"⚠️ Restriction Conflict: '{s_name}' contains beef/meat.")

                # Tally plate nutrition
                matched_item = foods_by_name.get(s_name)
                if matched_item:
                    current_plate_cals += matched_item.calories_kcal * s_qty
                    current_plate_prot += matched_item.protein_g * s_qty
                    current_plate_carbs += matched_item.carbs_g * s_qty
                    current_plate_fiber += matched_item.fiber_g * s_qty

            # Determine Smart Add-Ons based on current plate deficit & health goal
            # Case A: Low protein for Muscle Gain / High Protein goal
            if (health_goal in ['muscle_gain', 'high_protein', 'maintain']) and current_plate_prot < 20.0:
                # Find best high-protein safe add-on
                protein_candidates = sorted(
                    [f for f in safe_foods if f.protein_g >= 5.0 and f.food_name.lower() not in [sc.get("food_name","").lower() for sc in scanned_items]],
                    key=lambda x: x.protein_g,
                    reverse=True
                )
                if protein_candidates:
                    best_p = protein_candidates[0]
                    smart_add_ons.append(PlateAddOnSuggestion(
                        item=best_p,
                        why_add=f"+{best_p.protein_g}g Protein boost for your {health_goal.replace('_', ' ').title()} target.",
                        benefit_type="protein"
                    ))

            # Case B: Low fiber / High Glycemic Load
            if current_plate_fiber < 3.0 and current_plate_carbs > 40.0:
                fiber_candidates = sorted(
                    [f for f in safe_foods if f.fiber_g >= 2.0 and f.food_name.lower() not in [sc.get("food_name","").lower() for sc in scanned_items]],
                    key=lambda x: x.fiber_g,
                    reverse=True
                )
                if fiber_candidates:
                    best_fib = fiber_candidates[0]
                    smart_add_ons.append(PlateAddOnSuggestion(
                        item=best_fib,
                        why_add=f"+{best_fib.fiber_g}g Dietary Fiber to balance meal glycemic load and digestion.",
                        benefit_type="fiber"
                    ))

        projected_rem = max(remaining_cals - current_plate_cals, 0.0)
        
        # Budget Status
        budget_status = "optimal"
        if (today_consumed_cals + current_plate_cals) > daily_target:
            budget_status = "exceeded"
            warnings.append(f"Calorie Warning: This meal exceeds your remaining daily budget by {((today_consumed_cals + current_plate_cals) - daily_target):.0f} kcal.")
        elif projected_rem < (daily_target * 0.2):
            budget_status = "approaching_limit"

        # 6. Build Curated Goal-Aligned Meal Combos from Available Menu
        recommended_combos = self._build_goal_combos(safe_foods, remaining_cals, health_goal, diet_type)

        # 7. Generate Personalized Motivational Health Nudge
        health_nudge = self._generate_health_nudge(
            emp_name=emp_name,
            health_goal=health_goal,
            bmi_cat=bmi_cat,
            remaining_cals=remaining_cals,
            plate_cals=current_plate_cals,
            plate_prot=current_plate_prot,
            budget_status=budget_status
        )

        return PersonalizedRecommendationResponse(
            success=True,
            employee_code=emp.get("employee_code") or employee_code,
            employee_name=emp_name,
            department=department,
            health_goal=health_goal,
            diet_type=diet_type,
            bmi=bmi,
            bmi_category=bmi_cat,
            dietary_restrictions=restrictions,
            budget_status=NutritionalBudgetStatus(
                daily_target_calories=round(daily_target, 1),
                today_consumed_calories=round(today_consumed_cals, 1),
                remaining_calories=round(remaining_cals, 1),
                current_plate_calories=round(current_plate_cals, 1),
                projected_remaining_calories=round(projected_rem, 1),
                budget_status=budget_status
            ),
            recommended_combos=recommended_combos,
            smart_add_ons=smart_add_ons,
            warnings=warnings,
            health_nudge=health_nudge
        )

    def _build_goal_combos(
        self,
        safe_foods: List[FoodRecommendationItem],
        remaining_cals: float,
        health_goal: str,
        diet_type: str
    ) -> List[MealCombo]:
        """Builds 3 structured, nutritionally balanced Sri Lankan meal combinations."""
        combos: List[MealCombo] = []
        if not safe_foods:
            return combos

        food_map = {f.food_name.lower(): f for f in safe_foods}

        # Helper to pick existing items
        def pick(names: List[str]) -> List[FoodRecommendationItem]:
            res = []
            for n in names:
                for k, v in food_map.items():
                    if n.lower() in k:
                        res.append(v)
                        break
            return res

        # Combo 1: Goal-Tailored Signature Combo
        if health_goal in ['muscle_gain', 'high_protein']:
            c1_items = pick(['rice', 'chicken', 'dhal', 'sambol']) or pick(['rice', 'fish', 'dhal']) or safe_foods[:3]
            c1_title = "💪 Muscle Builder High-Protein Plate"
            c1_desc = "High-protein formulation optimized for lean muscle synthesis and physical performance."
            c1_tag = "Optimal for Muscle Gain"
        elif health_goal in ['weight_loss', 'low_carb']:
            c1_items = pick(['hopper', 'dhal', 'sambol']) or pick(['dhal', 'fish', 'sambol']) or safe_foods[:2]
            c1_title = "🥗 Slim & Fit Calorie-Deficit Plate"
            c1_desc = "Low glycemic density plate designed for sustained satiety with minimum caloric load."
            c1_tag = "Weight Loss Approved"
        else:
            c1_items = pick(['rice', 'fish', 'dhal', 'sambol']) or pick(['rice', 'dhal', 'sambol']) or safe_foods[:3]
            c1_title = "🍛 Traditional Balanced Canteen Combo"
            c1_desc = "WHO-calibrated Sri Lankan meal providing balanced energy, complete protein, and dietary fiber."
            c1_tag = "Balanced Daily Energy"

        c1 = self._assemble_combo("combo-1", c1_title, c1_desc, c1_items, 98, c1_tag)
        combos.append(c1)

        # Combo 2: High-Energy Active Workforce Plate
        c2_items = pick(['rice', 'dhal', 'egg', 'sambol']) or pick(['noodle', 'chicken']) or safe_foods[1:4] or safe_foods[:2]
        c2 = self._assemble_combo(
            "combo-2",
            "⚡ High-Protein Vegetarian / Energy Plate" if diet_type == 'vegetarian' else "🍗 Power Protein Lunch Plate",
            "Rich in essential amino acids and complex carbohydrates for high cognitive stamina.",
            c2_items,
            94,
            "High Protein & Satiety"
        )
        combos.append(c2)

        # Combo 3: Light Nutrient-Dense Specialty
        c3_items = pick(['roti', 'dhal', 'sambol']) or pick(['hopper', 'sambol']) or safe_foods[:2]
        c3 = self._assemble_combo(
            "combo-3",
            "🌿 Light Nutrient-Dense Snack & Lunch",
            "Quick, easily digestible meal packed with essential vitamins and dietary fiber.",
            c3_items,
            91,
            "Low Calorie & Light"
        )
        combos.append(c3)

        return combos

    def _assemble_combo(
        self,
        combo_id: str,
        title: str,
        description: str,
        items: List[FoodRecommendationItem],
        score: int,
        tag: str
    ) -> MealCombo:
        tot_cals = sum(it.calories_kcal for it in items)
        tot_price = sum(it.price_lkr for it in items)
        tot_prot = sum(it.protein_g for it in items)
        tot_carbs = sum(it.carbs_g for it in items)
        tot_fat = sum(it.fat_g for it in items)
        tot_fib = sum(it.fiber_g for it in items)

        return MealCombo(
            combo_id=combo_id,
            title=title,
            description=description,
            items=items,
            total_calories=round(tot_cals, 1),
            total_price_lkr=round(tot_price, 2),
            formatted_total_price=f"Rs. {tot_price:.2f}",
            total_protein_g=round(tot_prot, 1),
            total_carbs_g=round(tot_carbs, 1),
            total_fat_g=round(tot_fat, 1),
            total_fiber_g=round(tot_fib, 1),
            match_score=score,
            goal_alignment_tag=tag
        )

    def _generate_health_nudge(
        self,
        emp_name: str,
        health_goal: str,
        bmi_cat: str,
        remaining_cals: float,
        plate_cals: float,
        plate_prot: float,
        budget_status: str
    ) -> str:
        first_name = emp_name.split()[0] if emp_name else "Staff"

        if budget_status == "exceeded":
            return f"{first_name}, this meal exceeds your remaining daily energy allowance. Consider choosing smaller portion sizes or light greens for your next snack."

        if health_goal in ['muscle_gain', 'high_protein']:
            if plate_prot >= 20.0:
                return f"Excellent choice, {first_name}! Your current meal delivers {plate_prot:.1f}g protein, perfectly supporting your muscle recovery target."
            return f"{first_name}, you have {remaining_cals:.0f} kcal remaining today. Adding a high-protein item will help reach your daily muscle-building threshold."

        if health_goal in ['weight_loss', 'low_carb']:
            return f"Great progress, {first_name}! You have {remaining_cals:.0f} kcal remaining in your daily budget. Pairing complex carbohydrates with green sambol keeps satiety high."

        return f"Hello {first_name}, you have {remaining_cals:.0f} kcal remaining today. Enjoy a balanced meal with rich vitamins and hydration!"
