import urllib.request
import json

url = "http://localhost:8000/api/v1/employees/EMP001/full-profile"
with urllib.request.urlopen(url) as res:
    data = json.loads(res.read().decode())["data"]

print("========================================")
print("[+] LIVE PHASE 3 EMPLOYEE PROFILE API TEST")
print("========================================")
print(f"Employee Name : {data['name']} ({data['employee_code']})")
print(f"Department    : {data['department']}")
print(f"Work Email    : {data['email']}")
prof = data["profile"]
print(f"Biometrics    : {prof['age']} yrs | {prof['height_cm']} cm | {prof['weight_kg']} kg")
print(f"Dynamic BMI   : {prof['bmi']} -> {prof['bmi_category']}")
print(f"Calorie Target: {prof['daily_calorie_target']} kcal/day")
print(f"Diet / Goal   : {prof['diet_type']} | {prof['health_goal']}")
print("----------------------------------------")
print(f"Liked Foods   : {data['preferences']['likes']}")
print(f"Disliked Foods: {data['preferences']['dislikes']}")
print(f"Avoid Foods   : {data['preferences']['avoid']}")
print("========================================")
