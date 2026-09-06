import pytest
from src.profiles.validators import ProfileValidator
from src.profiles.schemas import BMICategory


def test_calculate_bmi():
    validator = ProfileValidator()
    
    # 170cm, 50kg -> BMI 17.3 (Underweight)
    res_under = validator.calculate_bmi(50.0, 170.0)
    assert res_under.bmi == 17.3
    assert res_under.category == BMICategory.UNDERWEIGHT

    # 170cm, 65kg -> BMI 22.5 (Normal)
    res_norm = validator.calculate_bmi(65.0, 170.0)
    assert res_norm.bmi == 22.5
    assert res_norm.category == BMICategory.NORMAL

    # 170cm, 80kg -> BMI 27.7 (Overweight)
    res_over = validator.calculate_bmi(80.0, 170.0)
    assert res_over.bmi == 27.7
    assert res_over.category == BMICategory.OVERWEIGHT

    # 170cm, 95kg -> BMI 32.9 (Obese)
    res_obese = validator.calculate_bmi(95.0, 170.0)
    assert res_obese.bmi == 32.9
    assert res_obese.category == BMICategory.OBESE


def test_validate_biometrics_invalid_ranges():
    validator = ProfileValidator()

    # Invalid Age
    with pytest.raises(ValueError, match="Age"):
        validator.validate_biometrics(age=10, height_cm=170, weight_kg=70, calorie_target=2000)

    # Invalid Height
    with pytest.raises(ValueError, match="Height"):
        validator.validate_biometrics(age=30, height_cm=50, weight_kg=70, calorie_target=2000)

    # Invalid Weight
    with pytest.raises(ValueError, match="Weight"):
        validator.validate_biometrics(age=30, height_cm=170, weight_kg=10, calorie_target=2000)

    # Invalid Calorie Target
    with pytest.raises(ValueError, match="Daily calorie target"):
        validator.validate_biometrics(age=30, height_cm=170, weight_kg=70, calorie_target=500)
