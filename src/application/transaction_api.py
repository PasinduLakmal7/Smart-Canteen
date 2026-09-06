"""
FastAPI REST API Routes for Phase 5 Meal History & Transactions Subsystem.
Provides endpoints for recording meals, querying employee history, and generating canteen analytics.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Body, Depends

from src.transactions.schemas import (
    TransactionCreateRequest,
    TransactionResponse,
    EmployeeMealHistoryResponse,
    MonthlySummaryResponse,
    CanteenAnalyticsSummary
)
from src.transactions.service import TransactionService
from src.utils.logging import app_logger

transaction_router = APIRouter(prefix="/api/v1", tags=["Meal History & Transactions"])

# Dependency singleton
transaction_service = TransactionService()


# ============================================================================
# 1. TRANSACTION CREATION & DETAILS
# ============================================================================

@transaction_router.post("/meal-transactions", response_model=Dict[str, Any], status_code=201)
async def create_meal_transaction(request: TransactionCreateRequest):
    """
    Creates an immutable meal transaction and calculates all pricing and nutrition server-side.
    Consumes outputs from Phase 1 (Food Vision), Phase 2 (Pricing), and Phase 4 (Face ID).
    """
    try:
        tx_response = transaction_service.create_transaction(request)
        return {"success": True, "transaction": tx_response.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        app_logger.error(f"Error creating transaction: {e}")
        raise HTTPException(status_code=500, detail=f"Transaction processing failed: {str(e)}")


@transaction_router.get("/meal-transactions", response_model=Dict[str, Any])
async def list_meal_transactions(
    employee_id: Optional[int] = Query(None, description="Filter by employee ID"),
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    department: Optional[str] = Query(None, description="Filter by department"),
    payment_status: Optional[str] = Query(None, description="Filter by payment status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """
    Lists canteen transactions with flexible filters for Admin reporting.
    """
    txs = transaction_service.list_all_transactions(
        employee_id=employee_id,
        date_str=date,
        department=department,
        payment_status=payment_status,
        limit=limit,
        offset=offset
    )
    return {
        "success": True,
        "count": len(txs),
        "transactions": [t.model_dump() for t in txs]
    }


@transaction_router.get("/meal-transactions/{id_or_code}", response_model=Dict[str, Any])
async def get_meal_transaction(id_or_code: str):
    """
    Retrieves full transaction details by numeric ID or transaction code (e.g. TX-20260905-0001).
    """
    tx = transaction_service.get_transaction(id_or_code)
    if not tx:
        raise HTTPException(status_code=404, detail=f"Transaction '{id_or_code}' not found.")
    return {"success": True, "transaction": tx.model_dump()}


# ============================================================================
# 2. EMPLOYEE MEAL HISTORY & PERSONAL SUMMARIES
# ============================================================================

@transaction_router.get("/employees/{id_or_code}/meal-history", response_model=Dict[str, Any])
async def get_employee_meal_history(
    id_or_code: str,
    date: Optional[str] = Query(None, description="Filter by specific date (YYYY-MM-DD)"),
    month: Optional[str] = Query(None, description="Filter by month (YYYY-MM)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """
    Returns personal meal history and daily intake logs for an employee.
    """
    try:
        history = transaction_service.get_employee_meal_history(
            id_or_code=id_or_code,
            date_filter=date,
            month_filter=month,
            limit=limit,
            offset=offset
        )
        return {"success": True, "data": history.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        app_logger.error(f"Error fetching meal history for {id_or_code}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch meal history: {str(e)}")


@transaction_router.get("/employees/{id_or_code}/meal-history/summary", response_model=Dict[str, Any])
async def get_employee_monthly_summary(
    id_or_code: str,
    month: Optional[str] = Query(None, description="Target month in YYYY-MM format")
):
    """
    Returns aggregated monthly calorie consumption, spend, and macro distribution for an employee.
    Used for Phase 6 personalized health recommendations.
    """
    try:
        summary = transaction_service.get_employee_monthly_summary(id_or_code=id_or_code, month=month)
        return {"success": True, "data": summary.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        app_logger.error(f"Error fetching monthly summary for {id_or_code}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate monthly summary: {str(e)}")


# ============================================================================
# 3. GLOBAL CANTEEN ANALYTICS
# ============================================================================

@transaction_router.get("/analytics/canteen-summary", response_model=Dict[str, Any])
async def get_canteen_analytics():
    """
    Returns global canteen KPIs: total transactions, total revenue in LKR, today's sales, and top dishes.
    """
    analytics = transaction_service.get_canteen_analytics()
    return {"success": True, "analytics": analytics.model_dump()}
