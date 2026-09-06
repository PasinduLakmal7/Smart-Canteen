import urllib.request
import json
from pathlib import Path

img_path = Path("data/raw/noodles/1.jpg")
if not img_path.exists():
    img_path = list(Path("data/raw").glob("*/*.jpg"))[0]

boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
with open(img_path, "rb") as f:
    img_bytes = f.read()

body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="{img_path.name}"\r\n'
    f"Content-Type: image/jpeg\r\n\r\n"
).encode("utf-8") + img_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

req = urllib.request.Request(
    "http://localhost:8000/api/v1/meal/analyze",
    data=body,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
)

with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode())

print("========================================")
print("[+] LIVE SMART CANTEEN MEAL ANALYSIS RESULT:")
print("========================================")
print(f"Total Bill Amount: {data['meal_totals']['formatted_total_bill']}")
print(f"Total Items Count: {data['meal_totals']['total_items_count']}")
print(f"Total Energy     : {data['meal_totals']['calories_kcal']} kcal")
print(f"Total Protein    : {data['meal_totals']['protein_g']} g")
print(f"Total Carbs      : {data['meal_totals']['carbs_g']} g")
print(f"Total Fat        : {data['meal_totals']['fat_g']} g")
print(f"Energy Ratios    : Protein {data['meal_totals']['protein_energy_pct']}% | Carbs {data['meal_totals']['carbs_energy_pct']}% | Fat {data['meal_totals']['fat_energy_pct']}%")
print("----------------------------------------")
print("Itemized Table Breakdown:")
for it in data["items"]:
    print(f" * {it['display_name']} (Qty: {it['quantity']}) => {it['formatted_total_price']} | {it['calories_kcal']} kcal | {it['protein_g']}g Prot")
print("========================================")
