import io
import os
import base64
import json
import yaml
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import cv2
import numpy as np
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.responses import HTMLResponse, JSONResponse

from src.utils.paths import (
    PRODUCTION_MODEL_PATH, MODEL_REGISTRY_PATH, MANIFEST_PATH,
    CLASSES_CONFIG_PATH, ensure_dir
)
from src.utils.logging import app_logger
from src.inference.detector import FoodDetector
from src.inference.image_predictor import draw_annotations

from database.connection import init_database
from database.seed.seed_runner import seed_database_if_empty
from src.foods.service import FoodService
from src.nutrition.service import NutritionService
from src.billing.service import BillingService
from src.meal_analysis.service import MealAnalysisService
from src.profiles.employee_service import EmployeeService
from src.profiles.profile_service import ProfileService
from src.face_recognition.service import FaceRecognitionService
from src.application.admin_api import admin_router
from src.application.profile_api import profile_router
from src.application.face_api import face_router
from src.application.transaction_api import transaction_router
from src.application.recommendation_api import recommendation_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Smart Canteen AI — Food Recognition, Nutrition, Biometrics, Profiles, Transactions & Recommendations",
    version="6.0.0",
    description="Multi-Modal AI System for Real-time Food Recognition, Automated Billing, Face Biometrics, Employee Profiles, Meal History & Personalized Recommendations."
)

# Enable CORS for React Frontends (Kiosk & Admin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(admin_router)
app.include_router(profile_router)
app.include_router(face_router)
app.include_router(transaction_router)
app.include_router(recommendation_router)


# Service Singletons
food_service = FoodService()
nutrition_service = NutritionService()
billing_service = BillingService()
meal_analysis_service = MealAnalysisService()
employee_service = EmployeeService()
profile_service = ProfileService()
face_service = FaceRecognitionService()

# Lazy-loaded FoodDetector instance
_detector = None


def get_detector() -> FoodDetector:
    global _detector
    if _detector is None:
        if not PRODUCTION_MODEL_PATH.exists():
            raise FileNotFoundError(
                "Production model best.pt not found. Please ensure best.pt is in models/production/best.pt."
            )
        _detector = FoodDetector(model_path=PRODUCTION_MODEL_PATH)
    return _detector


@app.on_event("startup")
async def startup_event():
    """Initializes SQLite database and seeds initial food & nutrition & employee data on server start."""
    try:
        init_database()
        seed_count = seed_database_if_empty()
        app_logger.info("Smart Canteen Phase 4 ready. Database, Biometric Face & Employee services initialized.")
    except Exception as e:
        app_logger.error(f"Error during startup database initialization: {e}")


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serves the Smart Canteen Phase 4 Web Application Interface."""
    return HTML_DASHBOARD_TEMPLATE


@app.get("/api/status")
async def get_system_status():
    """Returns dataset status, registered food classes, active employees, and face biometric status."""
    registry_data = {}
    if MODEL_REGISTRY_PATH.exists():
        try:
            with open(MODEL_REGISTRY_PATH, "r", encoding="utf-8") as f:
                registry_data = json.load(f)
        except Exception:
            pass

    foods = food_service.list_foods(active_only=True)
    employees = employee_service.list_employees(active_only=True)
    enrolled_faces = face_service.list_enrolled_employees()
    return {
        "production_model_available": PRODUCTION_MODEL_PATH.exists(),
        "production_model": registry_data.get("production_model"),
        "total_active_foods": len(foods),
        "total_active_employees": len(employees),
        "total_enrolled_faces": len(enrolled_faces),
        "foods": [f["class_name"] for f in foods]
    }


@app.get("/api/v1/foods")
async def list_active_foods():
    """Lists all active food items with their current price and nutrition facts."""
    foods = food_service.list_foods(active_only=True)
    results = []
    for f in foods:
        fid = f["id"]
        price_rec = billing_service.billing_repo.get_current_price_by_food_id(fid)
        nutr_rec = nutrition_service.nutrition_repo.get_by_food_id(fid)
        results.append({
            **f,
            "current_price": price_rec["price"] if price_rec else None,
            "nutrition": nutr_rec
        })
    return {"success": True, "foods": results}


@app.get("/api/v1/foods/{food_name}")
async def get_food_detail(food_name: str):
    """Retrieves full metadata, nutrition, and pricing for a specific food item."""
    food = food_service.get_food(food_name)
    if not food:
        raise HTTPException(status_code=404, detail=f"Food '{food_name}' not found in active menu.")
    
    fid = food["id"]
    price_rec = billing_service.billing_repo.get_current_price_by_food_id(fid)
    nutr_rec = nutrition_service.nutrition_repo.get_by_food_id(fid)
    return {
        "success": True,
        "food": food,
        "price": price_rec,
        "nutrition": nutr_rec
    }


@app.post("/api/v1/nutrition/calculate")
async def calculate_nutrition_endpoint(items: List[Dict[str, Any]] = Body(...)):
    """Computes nutrition breakdown for custom food quantities."""
    res = nutrition_service.calculate_meal_nutrition(items)
    return {"success": True, "data": res}


@app.post("/api/v1/billing/calculate")
async def calculate_billing_endpoint(
    items: List[Dict[str, Any]] = Body(...),
    discount: float = 0.0,
    tax: float = 0.0
):
    """Computes itemized and total bill for custom food quantities."""
    res = billing_service.calculate_meal_bill(items, discount=discount, tax=tax)
    return {"success": True, "data": res}


@app.post("/api/v1/meal/analyze")
@app.post("/api/detect")
async def analyze_meal_endpoint(file: UploadFile = File(...)):
    """
    Master Phase 2 Endpoint:
    Accepts food tray image -> YOLO Object Detection -> Nutrition Calculation -> Automated Billing -> UI Breakdown.
    """
    try:
        contents = await file.read()
        pil_img = Image.open(io.BytesIO(contents)).convert("RGB")
        bgr_frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        detector = get_detector()
        det_start = time.perf_counter()
        detections = detector.detect(bgr_frame)
        det_latency = round((time.perf_counter() - det_start) * 1000, 2)

        # Draw bounding boxes
        annotated_bgr = draw_annotations(bgr_frame, detections)
        _, buffer = cv2.imencode(".jpg", annotated_bgr)
        annotated_base64 = base64.b64encode(buffer).decode("utf-8")
        img_data_url = f"data:image/jpeg;base64,{annotated_base64}"

        # Run unified Meal Analysis (Nutrition + Billing)
        analysis_result = meal_analysis_service.analyze_detections(
            raw_detections=detections,
            annotated_image_base64=img_data_url
        )
        analysis_result.execution_latencies_ms["detection_ms"] = det_latency

        return JSONResponse(analysis_result.model_dump())
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        app_logger.error(f"Meal Analysis API error: {e}")
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")


HTML_DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Canteen AI — Food Recognition, Nutrition & Biometric Kiosk</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #090d16;
            --surface: rgba(20, 27, 45, 0.75);
            --surface-card: rgba(28, 38, 64, 0.6);
            --border: rgba(255, 255, 255, 0.08);
            --border-highlight: rgba(56, 189, 248, 0.3);
            --primary: #38bdf8;
            --primary-glow: rgba(56, 189, 248, 0.3);
            --accent-green: #22c55e;
            --accent-orange: #f97316;
            --accent-purple: #a855f7;
            --text: #f8fafc;
            --muted: #94a3b8;
            --danger: #ef4444;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Outfit', sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            background-image: 
                radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.08) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(34, 197, 94, 0.06) 0px, transparent 50%);
        }
        header {
            padding: 16px 36px;
            background: rgba(9, 13, 22, 0.85);
            backdrop-filter: blur(16px);
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 50;
        }
        .logo-area { display: flex; align-items: center; gap: 14px; }
        .logo-badge {
            background: linear-gradient(135deg, #0284c7, #38bdf8);
            width: 44px; height: 44px; border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.6rem; font-weight: 700; color: #fff;
            box-shadow: 0 0 24px var(--primary-glow);
        }
        .brand-title { font-size: 1.25rem; font-weight: 700; color: #fff; letter-spacing: -0.02em; }
        .brand-sub { font-size: 0.8rem; color: var(--muted); }
        .nav-tabs { display: flex; gap: 8px; background: rgba(255, 255, 255, 0.04); padding: 4px; border-radius: 12px; }
        .tab-btn {
            padding: 8px 18px; border: none; background: transparent;
            color: var(--muted); font-size: 0.9rem; font-weight: 500;
            border-radius: 8px; cursor: pointer; transition: all 0.2s;
            font-family: 'Outfit', sans-serif;
        }
        .tab-btn.active {
            background: var(--primary);
            color: #000;
            font-weight: 600;
            box-shadow: 0 0 16px var(--primary-glow);
        }
        main {
            flex: 1;
            padding: 30px;
            max-width: 1500px;
            margin: 0 auto;
            width: 100%;
        }
        .grid-layout {
            display: grid;
            grid-template-columns: 1.05fr 1.35fr;
            gap: 28px;
        }
        @media (max-width: 1050px) {
            .grid-layout { grid-template-columns: 1fr; }
        }
        .card {
            background: var(--surface);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 24px;
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35);
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }
        .card-title { font-size: 1.15rem; font-weight: 600; color: #fff; display: flex; align-items: center; gap: 8px; }
        
        .dropzone {
            border: 2px dashed rgba(56, 189, 248, 0.3);
            border-radius: 16px;
            padding: 36px 20px;
            text-align: center;
            background: rgba(56, 189, 248, 0.02);
            cursor: pointer;
            transition: all 0.25s ease;
        }
        .dropzone:hover {
            border-color: var(--primary);
            background: rgba(56, 189, 248, 0.06);
            transform: translateY(-2px);
        }
        .dropzone-icon { font-size: 2.8rem; margin-bottom: 10px; }
        .dropzone-text { font-size: 1.05rem; font-weight: 600; color: #fff; margin-bottom: 4px; }
        .dropzone-sub { font-size: 0.8rem; color: var(--muted); }
        .hidden-input { display: none; }

        .preview-box {
            margin-top: 20px;
            border-radius: 14px;
            overflow: hidden;
            border: 1px solid var(--border);
            background: #000;
            display: none;
            position: relative;
        }
        .preview-img { width: 100%; display: block; max-height: 480px; object-fit: contain; }
        
        /* Bill Banner */
        .bill-banner {
            background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(56, 189, 248, 0.12));
            border: 1px solid rgba(34, 197, 94, 0.35);
            border-radius: 16px;
            padding: 18px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .bill-left { display: flex; flex-direction: column; }
        .bill-label { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); font-weight: 600; }
        .bill-amount { font-size: 2.2rem; font-weight: 800; color: #4ade80; letter-spacing: -0.02em; }
        .bill-items-badge {
            background: rgba(34, 197, 94, 0.2);
            color: #4ade80;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }

        /* Biometric Identity Card */
        .identity-banner {
            background: linear-gradient(135deg, rgba(56, 189, 248, 0.15), rgba(168, 85, 247, 0.12));
            border: 1px solid rgba(56, 189, 248, 0.35);
            border-radius: 16px;
            padding: 18px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .identity-left { display: flex; align-items: center; gap: 16px; }
        .identity-avatar {
            width: 52px; height: 52px; border-radius: 50%;
            background: linear-gradient(135deg, #38bdf8, #818cf8);
            display: flex; align-items: center; justify-content: center;
            font-size: 1.6rem; color: #fff; font-weight: 700;
            box-shadow: 0 0 20px rgba(56, 189, 248, 0.3);
        }
        .identity-name { font-size: 1.25rem; font-weight: 700; color: #fff; }
        .identity-sub { font-size: 0.82rem; color: var(--muted); }
        .match-badge {
            padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;
            display: inline-flex; align-items: center; gap: 6px;
        }
        .match-badge.verified { background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.4); }
        .match-badge.unknown { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }

        /* Macro Metrics Row */
        .macro-row {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 22px;
        }
        .macro-card {
            background: var(--surface-card);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 14px;
            text-align: center;
        }
        .macro-card.cal { border-color: rgba(249, 115, 22, 0.3); background: rgba(249, 115, 22, 0.05); }
        .macro-card.prot { border-color: rgba(56, 189, 248, 0.3); background: rgba(56, 189, 248, 0.05); }
        .macro-card.carb { border-color: rgba(168, 85, 247, 0.3); background: rgba(168, 85, 247, 0.05); }
        .macro-card.fat { border-color: rgba(234, 179, 8, 0.3); background: rgba(234, 179, 8, 0.05); }
        .macro-val { font-size: 1.35rem; font-weight: 700; margin-top: 2px; }
        .macro-lbl { font-size: 0.75rem; color: var(--muted); font-weight: 500; text-transform: uppercase; }

        /* Itemized Food Table */
        .table-wrap {
            overflow-x: auto;
            margin-bottom: 20px;
            border-radius: 12px;
            border: 1px solid var(--border);
        }
        table { width: 100%; border-collapse: collapse; font-size: 0.9rem; text-align: left; }
        th { background: rgba(255, 255, 255, 0.03); padding: 12px 14px; color: var(--muted); font-weight: 600; border-bottom: 1px solid var(--border); }
        td { padding: 12px 14px; border-bottom: 1px solid rgba(255, 255, 255, 0.04); }
        tr:last-child td { border-bottom: none; }
        
        .meta-footer {
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: var(--muted);
            padding-top: 12px;
            border-top: 1px solid rgba(255, 255, 255, 0.06);
        }

        /* Form elements */
        .form-group { margin-bottom: 16px; }
        .form-label { display: block; font-size: 0.85rem; color: var(--muted); margin-bottom: 6px; font-weight: 500; }
        .input-box, select.input-box {
            width: 100%; padding: 10px 14px; background: rgba(0,0,0,0.3);
            border: 1px solid var(--border); border-radius: 10px;
            color: #fff; font-family: 'Outfit', sans-serif; font-size: 0.95rem;
        }
        .input-box:focus { outline: none; border-color: var(--primary); }
        .btn {
            background: linear-gradient(135deg, #0284c7, #38bdf8);
            color: #000; border: none; font-weight: 600; padding: 10px 20px;
            border-radius: 10px; cursor: pointer; transition: all 0.2s; font-family: 'Outfit', sans-serif;
        }
        .btn:hover { opacity: 0.9; transform: translateY(-1px); }

        .spinner {
            display: inline-block;
            width: 24px; height: 24px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: var(--primary);
            animation: spin 1s ease-in-out infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <header>
        <div class="logo-area">
            <div class="logo-badge">🍛</div>
            <div>
                <div class="brand-title">Smart Canteen AI</div>
                <div class="brand-sub">Multi-Modal Food Recognition, Nutrition & Biometric Kiosk (Phase 4)</div>
            </div>
        </div>
        <div class="nav-tabs">
            <button class="tab-btn active" id="tabKiosk" onclick="switchTab('kiosk')">⚡ Smart Canteen Kiosk (Face + Plate)</button>
            <button class="tab-btn" id="tabScanner" onclick="switchTab('scanner')">🍲 Plate Scanner</button>
            <button class="tab-btn" id="tabFaceEnroll" onclick="switchTab('faceEnroll')">🪪 Face Enrollment</button>
            <button class="tab-btn" id="tabEmployees" onclick="switchTab('employees')">👤 Employee Profiles</button>
            <button class="tab-btn" id="tabAdmin" onclick="switchTab('admin')">⚙️ Menu Admin</button>
        </div>
    </header>

    <main>
        <!-- TAB 1: SMART CANTEEN KIOSK (DUAL FACE + PLATE SCANNER) -->
        <div id="kioskSection" class="grid-layout">
            <!-- Left: Dual Input (Face Camera + Plate Camera) -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title"><span>📸</span> Counter Cameras (Face & Plate)</div>
                    <div id="kioskStatusBadge" style="font-size: 0.8rem; color: #4ade80; font-weight: 600;">● Dual AI Ready</div>
                </div>

                <!-- Face Scanner Box -->
                <div style="margin-bottom: 20px;">
                    <div class="form-label" style="display:flex; justify-content:space-between;">
                        <span>👤 1. Customer Face Camera</span>
                        <span id="faceScanStatus" style="color:var(--muted);">Waiting for customer...</span>
                    </div>
                    <div class="dropzone" style="padding: 20px;" onclick="document.getElementById('kioskFaceInput').click()">
                        <div style="font-size: 1.8rem; margin-bottom: 4px;">📷</div>
                        <div class="dropzone-text" style="font-size: 0.95rem;">Scan Customer Face</div>
                        <div class="dropzone-sub">Click or capture face frame for Biometric 1:N Identification</div>
                        <input type="file" id="kioskFaceInput" class="hidden-input" accept="image/*" onchange="handleKioskFaceSelect(event)">
                    </div>
                </div>

                <!-- Food Plate Scanner Box -->
                <div>
                    <div class="form-label" style="display:flex; justify-content:space-between;">
                        <span>🍽️ 2. Food Plate Camera</span>
                        <span id="plateScanStatus" style="color:var(--muted);">Waiting for tray...</span>
                    </div>
                    <div class="dropzone" style="padding: 20px;" onclick="document.getElementById('kioskPlateInput').click()">
                        <div style="font-size: 1.8rem; margin-bottom: 4px;">🍛</div>
                        <div class="dropzone-text" style="font-size: 0.95rem;">Scan Meal Tray</div>
                        <div class="dropzone-sub">YOLO11 Object Detection & Nutrition Breakdown</div>
                        <input type="file" id="kioskPlateInput" class="hidden-input" accept="image/*" onchange="handleKioskPlateSelect(event)">
                    </div>
                </div>

                <div id="kioskLoadingBox" style="display:none; text-align:center; padding: 20px;">
                    <div class="spinner"></div>
                    <div style="margin-top:8px; color: var(--muted); font-size: 0.85rem;">Processing Biometric & Food Vision Engines...</div>
                </div>

                <div class="preview-box" id="kioskPlatePreview">
                    <img id="kioskPlateAnnotated" class="preview-img" alt="Annotated Plate">
                </div>
            </div>

            <!-- Right: Unified Canteen Transaction & Health Context -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title"><span>🧾</span> Biometric Identification & Canteen Receipt</div>
                    <span id="kioskLatencyBadge" style="font-size: 0.75rem; color: var(--muted);">Latency: --</span>
                </div>

                <!-- Identity Card Banner -->
                <div class="identity-banner" id="identityBanner">
                    <div class="identity-left">
                        <div class="identity-avatar" id="avatarLetter">?</div>
                        <div>
                            <div class="identity-name" id="kioskEmpName">Customer Not Identified</div>
                            <div class="identity-sub" id="kioskEmpDept">Scan face on left to load biometric profile</div>
                        </div>
                    </div>
                    <div class="match-badge unknown" id="kioskMatchBadge">Awaiting Face</div>
                </div>

                <!-- Health Goals & Daily Calorie Context -->
                <div id="kioskHealthContext" style="display:none; background: rgba(0,0,0,0.25); border-radius: 14px; padding: 14px; margin-bottom: 20px; border: 1px solid var(--border);">
                    <div style="display:flex; justify-content:space-between; margin-bottom: 8px; font-size: 0.85rem;">
                        <span>Daily Calorie Target: <b id="kioskCalTarget">2000 kcal</b></span>
                        <span id="kioskDietBadge" style="background: rgba(56,189,248,0.2); color:#38bdf8; padding: 2px 8px; border-radius: 6px; font-weight:600;">Normal Diet</span>
                    </div>
                    <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow:hidden;">
                        <div id="kioskCalProgress" style="width: 0%; height: 100%; background: #38bdf8; transition: width 0.4s;"></div>
                    </div>
                    <div style="font-size: 0.75rem; color: var(--muted); margin-top: 6px;" id="kioskCalProgressText">This meal: 0 kcal (0.0% of daily target)</div>
                </div>

                <!-- Total Bill Banner -->
                <div class="bill-banner">
                    <div class="bill-left">
                        <span class="bill-label">Total Canteen Bill</span>
                        <span class="bill-amount" id="kioskTotalBill">Rs. 0.00</span>
                    </div>
                    <div class="bill-items-badge" id="kioskItemsCount">0 Items</div>
                </div>

                <!-- Macronutrient Row -->
                <div class="macro-row">
                    <div class="macro-card cal">
                        <div class="macro-lbl">Energy</div>
                        <div class="macro-val" id="kioskCal" style="color: #fb923c;">0 <span style="font-size:0.75rem;">kcal</span></div>
                    </div>
                    <div class="macro-card prot">
                        <div class="macro-lbl">Protein</div>
                        <div class="macro-val" id="kioskProt" style="color: #38bdf8;">0.0 <span style="font-size:0.75rem;">g</span></div>
                    </div>
                    <div class="macro-card carb">
                        <div class="macro-lbl">Carbs</div>
                        <div class="macro-val" id="kioskCarb" style="color: #c084fc;">0.0 <span style="font-size:0.75rem;">g</span></div>
                    </div>
                    <div class="macro-card fat">
                        <div class="macro-lbl">Fat</div>
                        <div class="macro-val" id="kioskFat" style="color: #facc15;">0.0 <span style="font-size:0.75rem;">g</span></div>
                    </div>
                </div>

                <!-- Itemized Breakdown Table -->
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>Food Item</th>
                                <th>Qty</th>
                                <th>Unit Price</th>
                                <th>Item Total</th>
                                <th>Calories</th>
                            </tr>
                        </thead>
                        <tbody id="kioskMealTable">
                            <tr>
                                <td colspan="5" style="text-align:center; color:var(--muted); padding: 20px;">
                                    Scan face and food tray to generate itemized meal bill.
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB 2: PLATE SCANNER (PHASE 1 & 2) -->
        <div id="scannerSection" class="grid-layout" style="display:none;">
            <div class="card">
                <div class="card-header">
                    <div class="card-title"><span>📷</span> Food Tray Camera Scan</div>
                    <div style="font-size: 0.8rem; color: #4ade80; font-weight: 600;">● Model Active</div>
                </div>
                <div class="dropzone" onclick="document.getElementById('fileInput').click()">
                    <div class="dropzone-icon">📥</div>
                    <div class="dropzone-text">Click or Drag & Drop Food Plate Image</div>
                    <div class="dropzone-sub">Supports JPG, PNG (YOLO11 Edge Multi-Class Recognition)</div>
                    <input type="file" id="fileInput" class="hidden-input" accept="image/*" onchange="handleFileSelect(event)">
                </div>
                <div id="loadingBox" style="display:none; text-align:center; padding: 24px;">
                    <div class="spinner"></div>
                    <div style="margin-top:10px; color: var(--muted); font-size: 0.9rem;">Analyzing food items, nutrition & price...</div>
                </div>
                <div class="preview-box" id="previewBox">
                    <img id="annotatedImage" class="preview-img" alt="Annotated Detections">
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title"><span>🧾</span> Automated Bill & Nutrition Assessment</div>
                    <span id="scanLatencyBadge" style="font-size: 0.75rem; color: var(--muted);">Ready</span>
                </div>
                <div class="bill-banner">
                    <div class="bill-left">
                        <span class="bill-label">Total Canteen Bill</span>
                        <span class="bill-amount" id="totalBillDisplay">Rs. 0.00</span>
                    </div>
                    <div class="bill-items-badge" id="totalItemsCountBadge">0 Food Items</div>
                </div>
                <div class="macro-row">
                    <div class="macro-card cal">
                        <div class="macro-lbl">Energy</div>
                        <div class="macro-val" id="macroCal" style="color: #fb923c;">0 <span style="font-size:0.8rem;">kcal</span></div>
                    </div>
                    <div class="macro-card prot">
                        <div class="macro-lbl">Protein</div>
                        <div class="macro-val" id="macroProt" style="color: #38bdf8;">0.0 <span style="font-size:0.8rem;">g</span></div>
                    </div>
                    <div class="macro-card carb">
                        <div class="macro-lbl">Carbs</div>
                        <div class="macro-val" id="macroCarb" style="color: #c084fc;">0.0 <span style="font-size:0.8rem;">g</span></div>
                    </div>
                    <div class="macro-card fat">
                        <div class="macro-lbl">Total Fat</div>
                        <div class="macro-val" id="macroFat" style="color: #facc15;">0.0 <span style="font-size:0.8rem;">g</span></div>
                    </div>
                </div>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>Food Item</th>
                                <th>Qty</th>
                                <th>Unit Price</th>
                                <th>Item Total</th>
                                <th>Calories</th>
                                <th>Protein</th>
                            </tr>
                        </thead>
                        <tbody id="mealTableBody">
                            <tr>
                                <td colspan="6" style="text-align:center; color:var(--muted); padding: 24px;">
                                    Upload or scan a meal plate to compute itemized nutrition and billing.
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div class="meta-footer">
                    <div>Fiber: <b id="macroFib">0.0g</b> | Sugar: <b id="macroSug">0.0g</b> | Sodium: <b id="macroSod">0mg</b></div>
                    <div>Source: <b>MRI Sri Lanka / USDA Provenance</b></div>
                </div>
            </div>
        </div>

        <!-- TAB 3: BIOMETRIC FACE ENROLLMENT TAB -->
        <div id="faceEnrollSection" class="grid-layout" style="display:none;">
            <!-- Face Enrollment Form -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title"><span>🪪</span> Biometric Face Enrollment</div>
                    <span style="font-size: 0.8rem; color: #38bdf8;">128D Metric Embeddings</span>
                </div>
                <div class="form-group">
                    <label class="form-label">Select Employee</label>
                    <select class="input-box" id="enrollEmpSelect"></select>
                </div>
                <div class="form-group">
                    <label class="form-label">Sample Tag (Perspective)</label>
                    <select class="input-box" id="enrollSampleTag">
                        <option value="frontal">Frontal Facing (Standard)</option>
                        <option value="left">Left Angle (~15° - 30°)</option>
                        <option value="right">Right Angle (~15° - 30°)</option>
                        <option value="glasses">With Glasses / Lighting Var</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Face Photo</label>
                    <div class="dropzone" style="padding: 24px;" onclick="document.getElementById('enrollFaceFile').click()">
                        <div style="font-size: 2rem; margin-bottom: 6px;">📷</div>
                        <div class="dropzone-text" style="font-size: 0.95rem;">Upload Face Photo</div>
                        <div class="dropzone-sub">Single clear face, good lighting (>50px resolution)</div>
                        <input type="file" id="enrollFaceFile" class="hidden-input" accept="image/*" onchange="previewEnrollFace(event)">
                    </div>
                </div>
                <div id="enrollPreviewBox" style="display:none; text-align:center; margin-bottom: 16px;">
                    <img id="enrollPreviewImg" style="max-height: 180px; border-radius: 12px; border: 1px solid var(--border);" alt="Preview">
                </div>
                <button class="btn" style="width: 100%;" onclick="submitFaceEnrollment()">Register Biometric Sample</button>
            </div>

            <!-- Enrolled Gallery -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title"><span>👥</span> Active Biometric Registry</div>
                    <div>
                        <button class="btn" style="padding: 6px 12px; font-size: 0.8rem; margin-right: 8px;" onclick="showNewEmpModal()">✨ + New Employee + Face</button>
                        <span id="enrolledCountBadge" style="font-size: 0.8rem; color: #4ade80;">0 Enrolled</span>
                    </div>
                </div>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>Code</th>
                                <th>Employee</th>
                                <th>Dept</th>
                                <th>Samples</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody id="enrolledTableBody">
                            <tr><td colspan="5" style="text-align:center; color:var(--muted); padding: 20px;">Loading gallery...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB 4: EMPLOYEE PROFILES (PHASE 3) -->
        <div id="employeesSection" class="grid-layout" style="display:none;">
            <div class="card">
                <div class="card-header">
                    <div class="card-title"><span>👥</span> Registered Employees</div>
                    <button class="btn" style="padding: 6px 12px; font-size: 0.8rem;" onclick="showNewEmpModal()">✨ + Add Employee & Face</button>
                </div>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>Code</th>
                                <th>Name</th>
                                <th>Department</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody id="empTableBody">
                            <tr><td colspan="4" style="text-align:center; color:var(--muted); padding: 20px;">Loading employees...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title"><span>⚙️</span> Health & Nutrition Profile Editor</div>
                    <span id="selectedEmpBadge" style="font-size: 0.8rem; color: #38bdf8;">Select an employee</span>
                </div>
                <div id="profileFormWrap">
                    <p style="color:var(--muted); text-align:center; padding: 30px;">Select an employee from the left to view or edit biometrics and dietary preferences.</p>
                </div>
            </div>
        </div>

        <!-- TAB 5: ADMIN MENU & PRICES (PHASE 2) -->
        <div id="adminSection" class="card" style="display:none;">
            <div class="card-header">
                <div class="card-title"><span>🍽️</span> Canteen Food & Dynamic Pricing Catalog</div>
                <button class="btn" onclick="loadAdminFoods()">🔄 Refresh Catalog</button>
            </div>
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>Class Code</th>
                            <th>Display Name</th>
                            <th>Serving Type</th>
                            <th>Unit Price (LKR)</th>
                            <th>Calories (kcal)</th>
                            <th>Protein (g)</th>
                            <th>Status</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody id="adminTableBody">
                        <tr><td colspan="8" style="text-align:center; padding: 20px;">Loading catalog...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- UNIFIED MODAL: ADD EMPLOYEE & BIOMETRICS IN ONE WINDOW -->
        <div id="newEmpModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); backdrop-filter:blur(10px); z-index:999; align-items:center; justify-content:center;">
            <div class="card" style="max-width:680px; width:92%; max-height:90vh; overflow-y:auto; border: 1px solid var(--border-highlight); box-shadow: 0 20px 50px rgba(0,0,0,0.8);">
                <div class="card-header">
                    <div class="card-title"><span>✨</span> Register Employee & Face Biometrics (All-in-One)</div>
                    <button class="btn" style="background:transparent; color:#fff; font-size:1.2rem; padding:4px 8px;" onclick="closeNewEmpModal()">✕</button>
                </div>
                
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px;">
                    <div class="form-group">
                        <label class="form-label">Employee Code *</label>
                        <input type="text" class="input-box" id="newEmpCode" placeholder="e.g. EMP004">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Department *</label>
                        <input type="text" class="input-box" id="newEmpDept" placeholder="e.g. Engineering">
                    </div>
                    <div class="form-group">
                        <label class="form-label">First Name *</label>
                        <input type="text" class="input-box" id="newEmpFname" placeholder="e.g. Samantha">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Last Name *</label>
                        <input type="text" class="input-box" id="newEmpLname" placeholder="e.g. Rathnayake">
                    </div>
                </div>

                <div class="form-group">
                    <label class="form-label">Email Address *</label>
                    <input type="email" class="input-box" id="newEmpEmail" placeholder="e.g. samantha.r@canteen.lk">
                </div>

                <div style="border-top: 1px solid var(--border); margin: 16px 0; padding-top: 14px;">
                    <div style="font-weight:600; color:#38bdf8; margin-bottom:12px; font-size:0.95rem;">👤 Health Profile & Biometrics</div>
                    <div style="display:grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap:10px;">
                        <div class="form-group">
                            <label class="form-label">Age</label>
                            <input type="number" class="input-box" id="newEmpAge" value="28">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Height (cm)</label>
                            <input type="number" class="input-box" id="newEmpHeight" value="170">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Weight (kg)</label>
                            <input type="number" class="input-box" id="newEmpWeight" value="68">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Target (kcal)</label>
                            <input type="number" class="input-box" id="newEmpCal" value="2200">
                        </div>
                    </div>
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px;">
                        <div class="form-group">
                            <label class="form-label">Diet Type</label>
                            <select class="input-box" id="newEmpDiet">
                                <option value="normal">Normal</option>
                                <option value="vegetarian">Vegetarian</option>
                                <option value="vegan">Vegan</option>
                                <option value="pescatarian">Pescatarian</option>
                                <option value="halal">Halal</option>
                                <option value="diabetic">Diabetic</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Health Goal</label>
                            <select class="input-box" id="newEmpGoal">
                                <option value="maintain">Maintain Weight</option>
                                <option value="weight_loss">Weight Loss</option>
                                <option value="weight_gain">Weight Gain</option>
                                <option value="high_protein">High Protein</option>
                                <option value="low_carb">Low Carb</option>
                                <option value="heart_healthy">Heart Healthy</option>
                            </select>
                        </div>
                    </div>
                </div>

                <div style="border-top: 1px solid var(--border); margin: 16px 0; padding-top: 14px;">
                    <div style="font-weight:600; color:#4ade80; margin-bottom:8px; font-size:0.95rem;">📸 Biometric Face Enrollment (Attached Simultaneously)</div>
                    <div class="dropzone" style="padding: 16px;" onclick="document.getElementById('newEmpFaceFile').click()">
                        <div style="font-size: 1.6rem; margin-bottom: 4px;">📷</div>
                        <div class="dropzone-text" style="font-size: 0.9rem;">Click to Upload Face Photo</div>
                        <div class="dropzone-sub">Upload clear face photo to enroll biometric embedding right now</div>
                        <input type="file" id="newEmpFaceFile" class="hidden-input" accept="image/*" onchange="previewNewEmpFace(event)">
                    </div>
                    <div id="newEmpFacePreviewBox" style="display:none; text-align:center; margin-top: 10px;">
                        <img id="newEmpFacePreviewImg" style="max-height: 120px; border-radius: 10px; border: 1px solid var(--border);" alt="Face Preview">
                    </div>
                </div>

                <div style="display:flex; gap:10px; margin-top:20px;">
                    <button class="btn" style="flex:1;" onclick="submitNewEmployeeWithFace()">🚀 Complete Registration & Save Face</button>
                    <button class="btn" style="background:rgba(255,255,255,0.1); color:#fff;" onclick="closeNewEmpModal()">Cancel</button>
                </div>
            </div>
        </div>

    </main>

    <script>
        let currentKioskFace = null;
        let currentKioskPlate = null;
        let identifiedEmployee = null;

        function switchTab(tabId) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.getElementById('kioskSection').style.display = 'none';
            document.getElementById('scannerSection').style.display = 'none';
            document.getElementById('faceEnrollSection').style.display = 'none';
            document.getElementById('employeesSection').style.display = 'none';
            document.getElementById('adminSection').style.display = 'none';

            if (tabId === 'kiosk') {
                document.getElementById('tabKiosk').classList.add('active');
                document.getElementById('kioskSection').style.display = 'grid';
            } else if (tabId === 'scanner') {
                document.getElementById('tabScanner').classList.add('active');
                document.getElementById('scannerSection').style.display = 'grid';
            } else if (tabId === 'faceEnroll') {
                document.getElementById('tabFaceEnroll').classList.add('active');
                document.getElementById('faceEnrollSection').style.display = 'grid';
                loadFaceEnrollmentData();
            } else if (tabId === 'employees') {
                document.getElementById('tabEmployees').classList.add('active');
                document.getElementById('employeesSection').style.display = 'grid';
                loadEmployees();
            } else if (tabId === 'admin') {
                document.getElementById('tabAdmin').classList.add('active');
                document.getElementById('adminSection').style.display = 'block';
                loadAdminFoods();
            }
        }

        // ==========================================
        // SMART CANTEEN KIOSK (DUAL FACE + PLATE)
        // ==========================================
        async function handleKioskFaceSelect(e) {
            const file = e.target.files[0];
            if (!file) return;
            currentKioskFace = file;
            document.getElementById('faceScanStatus').innerText = 'Recognizing...';

            const formData = new FormData();
            formData.append('file', file);

            try {
                const res = await fetch('/api/v1/face/recognize', { method: 'POST', body: formData });
                const result = await res.json();
                const data = result.data;

                if (data.matched) {
                    identifiedEmployee = data;
                    document.getElementById('kioskEmpName').innerText = data.employee_name;
                    document.getElementById('kioskEmpDept').innerText = `${data.department} • Code: ${data.employee_code}`;
                    document.getElementById('avatarLetter').innerText = data.employee_name.charAt(0);
                    
                    const badge = document.getElementById('kioskMatchBadge');
                    badge.className = 'match-badge verified';
                    badge.innerText = `● Verified (${(data.confidence * 100).toFixed(1)}%)`;

                    document.getElementById('faceScanStatus').innerText = '✓ Identified';

                    // Health Goals context
                    if (data.employee_profile && data.employee_profile.profile) {
                        const prof = data.employee_profile.profile;
                        document.getElementById('kioskHealthContext').style.display = 'block';
                        document.getElementById('kioskCalTarget').innerText = `${prof.daily_calorie_target} kcal`;
                        document.getElementById('kioskDietBadge').innerText = `${prof.diet_type.toUpperCase()} • ${prof.health_goal}`;
                    }
                } else {
                    identifiedEmployee = null;
                    document.getElementById('kioskEmpName').innerText = 'Unknown Person';
                    document.getElementById('kioskEmpDept').innerText = data.message;
                    document.getElementById('avatarLetter').innerText = '✕';
                    
                    const badge = document.getElementById('kioskMatchBadge');
                    badge.className = 'match-badge unknown';
                    badge.innerText = `✕ Rejected (${(data.confidence * 100).toFixed(1)}%)`;
                    document.getElementById('faceScanStatus').innerText = '✕ Unknown';
                    document.getElementById('kioskHealthContext').style.display = 'none';
                }
            } catch (err) {
                alert('Face Recognition error: ' + err.message);
                document.getElementById('faceScanStatus').innerText = 'Error';
            }
        }

        async function handleKioskPlateSelect(e) {
            const file = e.target.files[0];
            if (!file) return;
            currentKioskPlate = file;
            document.getElementById('plateScanStatus').innerText = 'Analyzing meal...';
            document.getElementById('kioskLoadingBox').style.display = 'block';

            const formData = new FormData();
            formData.append('file', file);

            try {
                const res = await fetch('/api/v1/meal/analyze', { method: 'POST', body: formData });
                const data = await res.json();

                document.getElementById('kioskLoadingBox').style.display = 'none';
                document.getElementById('plateScanStatus').innerText = '✓ Plate Analyzed';

                // Display Annotated Image
                if (data.annotated_image) {
                    document.getElementById('kioskPlatePreview').style.display = 'block';
                    document.getElementById('kioskPlateAnnotated').src = data.annotated_image;
                }

                // Render Bill & Macros
                document.getElementById('kioskTotalBill').innerText = `Rs. ${(data.billing.total_bill_lkr || 0).toFixed(2)}`;
                document.getElementById('kioskItemsCount').innerText = `${data.detected_foods.length} Items`;

                const nutr = data.nutrition;
                document.getElementById('kioskCal').innerHTML = `${Math.round(nutr.total_calories_kcal)} <span style="font-size:0.75rem;">kcal</span>`;
                document.getElementById('kioskProt').innerHTML = `${nutr.total_protein_g.toFixed(1)} <span style="font-size:0.75rem;">g</span>`;
                document.getElementById('kioskCarb').innerHTML = `${nutr.total_carbs_g.toFixed(1)} <span style="font-size:0.75rem;">g</span>`;
                document.getElementById('kioskFat').innerHTML = `${nutr.total_fat_g.toFixed(1)} <span style="font-size:0.75rem;">g</span>`;

                // Update Progress if employee is identified
                if (identifiedEmployee && identifiedEmployee.employee_profile && identifiedEmployee.employee_profile.profile) {
                    const target = identifiedEmployee.employee_profile.profile.daily_calorie_target;
                    const pct = Math.min(100, Math.round((nutr.total_calories_kcal / target) * 100));
                    document.getElementById('kioskCalProgress').style.width = `${pct}%`;
                    document.getElementById('kioskCalProgressText').innerText = `This meal: ${Math.round(nutr.total_calories_kcal)} kcal (${pct}% of daily ${target} kcal target)`;
                }

                // Render Table
                const tbody = document.getElementById('kioskMealTable');
                if (data.detected_foods.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--muted); padding: 20px;">No recognizable food items detected on tray.</td></tr>`;
                } else {
                    tbody.innerHTML = data.detected_foods.map(item => `
                        <tr>
                            <td><b>${item.display_name}</b></td>
                            <td>${item.quantity}</td>
                            <td>Rs. ${(item.unit_price_lkr || 0).toFixed(2)}</td>
                            <td><b>Rs. ${(item.item_total_lkr || 0).toFixed(2)}</b></td>
                            <td>${Math.round(item.calories_kcal)} kcal</td>
                        </tr>
                    `).join('');
                }
            } catch (err) {
                document.getElementById('kioskLoadingBox').style.display = 'none';
                alert('Meal Analysis error: ' + err.message);
            }
        }

        // ==========================================
        // FACE ENROLLMENT JAVASCRIPT
        // ==========================================
        let enrollFaceFileObj = null;

        async function loadFaceEnrollmentData() {
            // 1. Populate employees dropdown
            const res = await fetch('/api/v1/employees');
            const data = await res.json();
            const select = document.getElementById('enrollEmpSelect');
            select.innerHTML = data.employees.map(e => `<option value="${e.employee_code}">${e.employee_code} — ${e.first_name} ${e.last_name} (${e.department})</option>`).join('');

            // 2. Load enrolled gallery
            const galRes = await fetch('/api/v1/face/enrolled');
            const galData = await galRes.json();
            document.getElementById('enrolledCountBadge').innerText = `${galData.count} Enrolled`;

            const tbody = document.getElementById('enrolledTableBody');
            if (galData.enrolled_employees.length === 0) {
                tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--muted); padding: 20px;">No employees enrolled yet.</td></tr>`;
            } else {
                tbody.innerHTML = galData.enrolled_employees.map(emp => `
                    <tr>
                        <td><code>${emp.employee_code}</code></td>
                        <td><b>${emp.name}</b></td>
                        <td>${emp.department}</td>
                        <td><span style="background:rgba(56,189,248,0.15); color:#38bdf8; padding:2px 8px; border-radius:6px;">${emp.sample_count} samples (${emp.sample_tags.join(', ')})</span></td>
                        <td><button class="btn" style="background:#ef4444; color:#fff; padding:4px 10px; font-size:0.75rem;" onclick="deactivateFace('${emp.employee_code}')">Deactivate</button></td>
                    </tr>
                `).join('');
            }
        }

        function previewEnrollFace(e) {
            const file = e.target.files[0];
            if (!file) return;
            enrollFaceFileObj = file;
            const reader = new FileReader();
            reader.onload = (event) => {
                document.getElementById('enrollPreviewBox').style.display = 'block';
                document.getElementById('enrollPreviewImg').src = event.target.result;
            };
            reader.readAsDataURL(file);
        }

        async function submitFaceEnrollment() {
            if (!enrollFaceFileObj) {
                alert('Please choose a face photo to enroll.');
                return;
            }
            const empCode = document.getElementById('enrollEmpSelect').value;
            const tag = document.getElementById('enrollSampleTag').value;

            const formData = new FormData();
            formData.append('employee_code', empCode);
            formData.append('sample_tag', tag);
            formData.append('file', enrollFaceFileObj);

            try {
                const res = await fetch('/api/v1/face/register', { method: 'POST', body: formData });
                const data = await res.json();
                if (res.ok) {
                    alert('Face sample enrolled successfully!');
                    document.getElementById('enrollPreviewBox').style.display = 'none';
                    enrollFaceFileObj = null;
                    loadFaceEnrollmentData();
                } else {
                    alert('Enrollment failed: ' + (data.detail || 'Quality check failed'));
                }
            } catch (err) {
                alert('Error: ' + err.message);
            }
        }

        async function deactivateFace(empCode) {
            if (!confirm(`Are you sure you want to deactivate biometric face data for ${empCode}?`)) return;
            try {
                const res = await fetch(`/api/v1/face/${empCode}`, { method: 'DELETE' });
                if (res.ok) {
                    alert('Face biometric data deactivated.');
                    loadFaceEnrollmentData();
                } else {
                    alert('Failed to deactivate.');
                }
            } catch (err) {
                alert('Error: ' + err.message);
            }
        }

        // ==========================================
        // SCANNER (PHASE 1 & 2) JAVASCRIPT
        // ==========================================
        async function handleFileSelect(e) {
            const file = e.target.files[0];
            if (!file) return;
            document.getElementById('loadingBox').style.display = 'block';
            const formData = new FormData();
            formData.append('file', file);
            try {
                const res = await fetch('/api/v1/meal/analyze', { method: 'POST', body: formData });
                const data = await res.json();
                document.getElementById('loadingBox').style.display = 'none';
                if (data.annotated_image) {
                    document.getElementById('previewBox').style.display = 'block';
                    document.getElementById('annotatedImage').src = data.annotated_image;
                }
                document.getElementById('totalBillDisplay').innerText = `Rs. ${(data.billing.total_bill_lkr || 0).toFixed(2)}`;
                document.getElementById('totalItemsCountBadge').innerText = `${data.detected_foods.length} Items`;
                const nutr = data.nutrition;
                document.getElementById('macroCal').innerHTML = `${Math.round(nutr.total_calories_kcal)} <span style="font-size:0.8rem;">kcal</span>`;
                document.getElementById('macroProt').innerHTML = `${nutr.total_protein_g.toFixed(1)} <span style="font-size:0.8rem;">g</span>`;
                document.getElementById('macroCarb').innerHTML = `${nutr.total_carbs_g.toFixed(1)} <span style="font-size:0.8rem;">g</span>`;
                document.getElementById('macroFat').innerHTML = `${nutr.total_fat_g.toFixed(1)} <span style="font-size:0.8rem;">g</span>`;
                const tbody = document.getElementById('mealTableBody');
                tbody.innerHTML = data.detected_foods.map(item => `
                    <tr>
                        <td><b>${item.display_name}</b></td>
                        <td>${item.quantity}</td>
                        <td>Rs. ${(item.unit_price_lkr || 0).toFixed(2)}</td>
                        <td><b>Rs. ${(item.item_total_lkr || 0).toFixed(2)}</b></td>
                        <td>${Math.round(item.calories_kcal)} kcal</td>
                        <td>${item.protein_g.toFixed(1)}g</td>
                    </tr>
                `).join('');
            } catch (err) {
                document.getElementById('loadingBox').style.display = 'none';
                alert('Scan error: ' + err.message);
            }
        }

        // ==========================================
        // EMPLOYEE PROFILES JAVASCRIPT
        // ==========================================
        async function loadEmployees() {
            const res = await fetch('/api/v1/employees');
            const data = await res.json();
            const tbody = document.getElementById('empTableBody');
            tbody.innerHTML = data.employees.map(e => `
                <tr>
                    <td><code>${e.employee_code}</code></td>
                    <td><b>${e.first_name} ${e.last_name}</b></td>
                    <td>${e.department}</td>
                    <td><button class="btn" style="padding:4px 10px; font-size:0.75rem;" onclick="loadEmployeeProfile('${e.employee_code}')">Edit Profile</button></td>
                </tr>
            `).join('');
        }

        async function loadEmployeeProfile(code) {
            const res = await fetch(`/api/v1/employees/${code}/full-profile`);
            const result = await res.json();
            const full = result.data;
            document.getElementById('selectedEmpBadge').innerText = `${full.employee.first_name} ${full.employee.last_name} (${code})`;
            
            const prof = full.profile || {};
            const biometrics = prof.biometrics || {};
            const wrap = document.getElementById('profileFormWrap');
            wrap.innerHTML = `
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px;">
                    <div class="form-group">
                        <label class="form-label">Age</label>
                        <input type="number" class="input-box" id="profAge" value="${prof.age || 30}">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Daily Calorie Target (kcal)</label>
                        <input type="number" class="input-box" id="profCal" value="${prof.daily_calorie_target || 2000}">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Height (cm)</label>
                        <input type="number" class="input-box" id="profHeight" value="${biometrics.height_cm || 170}">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Weight (kg)</label>
                        <input type="number" class="input-box" id="profWeight" value="${biometrics.weight_kg || 70}">
                    </div>
                </div>
                <div class="form-group">
                    <label class="form-label">Calculated BMI: <b>${biometrics.bmi || '--'} (${biometrics.bmi_category || 'Normal'})</b></label>
                </div>
                <button class="btn" style="width:100%;" onclick="saveProfile(${full.employee.id})">Save Health Profile</button>
            `;
        }

        async function saveProfile(empId) {
            const age = parseInt(document.getElementById('profAge').value);
            const cal = parseFloat(document.getElementById('profCal').value);
            const height = parseFloat(document.getElementById('profHeight').value);
            const weight = parseFloat(document.getElementById('profWeight').value);

            try {
                const res = await fetch(`/api/v1/employees/${empId}/profile`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        age: age,
                        height_cm: height,
                        weight_kg: weight,
                        daily_calorie_target: cal
                    })
                });
                if (res.ok) {
                    alert('Profile updated successfully!');
                } else {
                    alert('Failed to update profile');
                }
            } catch (err) {
                alert('Error: ' + err.message);
            }
        }

        // ==========================================
        // ADMIN JAVASCRIPT
        // ==========================================
        async function loadAdminFoods() {
            const tbody = document.getElementById('adminTableBody');
            tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding: 20px;">Loading catalog...</td></tr>`;
            try {
                const res = await fetch('/api/v1/admin/foods');
                const foods = await res.json();
                tbody.innerHTML = foods.map(f => `
                    <tr>
                        <td><code>${f.class_name}</code></td>
                        <td><b>${f.display_name}</b></td>
                        <td>${f.serving_type}</td>
                        <td><input type="number" step="1.0" class="input-box" style="width:85px;" id="price_${f.id}" value="${f.current_price || 0}"></td>
                        <td>${f.nutrition ? f.nutrition.calories_kcal : 0}</td>
                        <td>${f.nutrition ? f.nutrition.protein_g : 0}</td>
                        <td><span style="color:${f.active ? '#4ade80':'#ef4444'}">${f.active ? 'Active':'Inactive'}</span></td>
                        <td><button class="btn" onclick="savePrice(${f.id})">Save</button></td>
                    </tr>
                `).join('');
            } catch (e) {
                tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:#ef4444; padding: 20px;">Error: ${e.message}</td></tr>`;
            }
        }

        // ==========================================
        // UNIFIED EMPLOYEE & FACE REGISTRATION MODAL JS
        // ==========================================
        let newEmpFaceFileObj = null;

        function showNewEmpModal() {
            document.getElementById('newEmpModal').style.display = 'flex';
            newEmpFaceFileObj = null;
            document.getElementById('newEmpFacePreviewBox').style.display = 'none';
        }

        function closeNewEmpModal() {
            document.getElementById('newEmpModal').style.display = 'none';
        }

        function previewNewEmpFace(e) {
            const file = e.target.files[0];
            if (!file) return;
            newEmpFaceFileObj = file;
            const reader = new FileReader();
            reader.onload = (event) => {
                document.getElementById('newEmpFacePreviewBox').style.display = 'block';
                document.getElementById('newEmpFacePreviewImg').src = event.target.result;
            };
            reader.readAsDataURL(file);
        }

        async function submitNewEmployeeWithFace() {
            const code = document.getElementById('newEmpCode').value.trim();
            const dept = document.getElementById('newEmpDept').value.trim();
            const fname = document.getElementById('newEmpFname').value.trim();
            const lname = document.getElementById('newEmpLname').value.trim();
            const email = document.getElementById('newEmpEmail').value.trim();

            if (!code || !fname || !lname || !dept || !email) {
                alert('Please fill all required basic employee fields (Code, Name, Department, Email).');
                return;
            }

            try {
                // 1. Create Employee
                const empRes = await fetch('/api/v1/employees', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        employee_code: code,
                        first_name: fname,
                        last_name: lname,
                        department: dept,
                        email: email
                    })
                });

                if (!empRes.ok) {
                    const err = await empRes.json();
                    alert('Failed to create employee: ' + (err.detail || 'Validation error'));
                    return;
                }

                const empData = await empRes.json();
                const empId = empData.employee.id;

                // 2. Set Health & Nutrition Profile
                const age = parseInt(document.getElementById('newEmpAge').value);
                const height = parseFloat(document.getElementById('newEmpHeight').value);
                const weight = parseFloat(document.getElementById('newEmpWeight').value);
                const cal = parseFloat(document.getElementById('newEmpCal').value);
                const diet = document.getElementById('newEmpDiet').value;
                const goal = document.getElementById('newEmpGoal').value;

                await fetch(`/api/v1/employees/${empId}/profile`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        age: age,
                        height_cm: height,
                        weight_kg: weight,
                        daily_calorie_target: cal,
                        diet_type: diet,
                        health_goal: goal
                    })
                });

                // 3. Attach Face Biometrics simultaneously if photo uploaded
                if (newEmpFaceFileObj) {
                    const faceFormData = new FormData();
                    faceFormData.append('employee_code', code);
                    faceFormData.append('sample_tag', 'frontal');
                    faceFormData.append('file', newEmpFaceFileObj);

                    const faceRes = await fetch('/api/v1/face/register', {
                        method: 'POST',
                        body: faceFormData
                    });

                    if (!faceRes.ok) {
                        const faceErr = await faceRes.json();
                        alert('Employee created, but face quality check returned: ' + (faceErr.detail || 'Quality issue'));
                    }
                }

                alert(`Success! Employee ${fname} ${lname} (${code}) and Biometric Face Profile registered successfully in one step!`);
                closeNewEmpModal();
                loadEmployees();
                loadFaceEnrollmentData();

            } catch (err) {
                alert('Error during registration: ' + err.message);
            }
        }
    </script>
</body>
</html>
"""
