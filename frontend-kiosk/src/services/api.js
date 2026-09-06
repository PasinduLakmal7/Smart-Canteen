/**
 * Smart Canteen AI — Kiosk API Client Layer
 * Connects directly to FastAPI backend via Vite proxy or direct URL
 */

const API_BASE = '/api/v1';

export const faceApi = {
  /**
   * Send face image for 128D SFace biometric recognition
   * @param {File|Blob} file 
   */
  async recognize(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const res = await fetch(`${API_BASE}/face/recognize`, {
      method: 'POST',
      body: formData,
    });
    
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Face recognition failed with status ${res.status}`);
    }
    const data = await res.json();
    return data.data || data;
  }
};

export const mealApi = {
  /**
   * Send food plate image for YOLO11n multi-class detection and nutrition assessment
   * @param {File|Blob} file 
   */
  async analyze(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const res = await fetch(`${API_BASE}/meal/analyze`, {
      method: 'POST',
      body: formData,
    });
    
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Meal analysis failed with status ${res.status}`);
    }
    const data = await res.json();
    return data.data || data;
  }
};

export const employeeApi = {
  /**
   * Fetch full employee profile including health goals, WHO BMI, dietary restrictions
   * @param {string} idOrCode 
   */
  async getProfile(idOrCode) {
    const res = await fetch(`${API_BASE}/employees/${idOrCode}/full-profile`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to fetch employee profile for ${idOrCode}`);
    }
    const data = await res.json();
    return data.data || data;
  }
};

export const transactionApi = {
  /**
   * Creates a meal transaction and payroll charge in the backend
   * @param {Object} payload 
   */
  async create(payload) {
    const res = await fetch(`${API_BASE}/meal-transactions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Transaction creation failed');
    }
    const data = await res.json();
    return data.transaction || data;
  },

  /**
   * Fetches an employee's personal meal history
   * @param {string} idOrCode 
   * @param {string} dateFilter 
   */
  async getHistory(idOrCode, dateFilter = null) {
    let url = `${API_BASE}/employees/${idOrCode}/meal-history`;
    if (dateFilter) url += `?date=${dateFilter}`;
    const res = await fetch(url);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to fetch meal history');
    }
    const data = await res.json();
    return data.data || data;
  },

  /**
   * Fetches monthly nutrition & spend summary for employee
   * @param {string} idOrCode 
   * @param {string} month 
   */
  async getMonthlySummary(idOrCode, month = null) {
    let url = `${API_BASE}/employees/${idOrCode}/meal-history/summary`;
    if (month) url += `?month=${month}`;
    const res = await fetch(url);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to fetch monthly summary');
    }
    const data = await res.json();
    return data.data || data;
  }
};

export const recommendationApi = {
  /**
   * Phase 6: Get personalized meal recommendations, smart plate add-ons & health nudges
   * @param {string} employeeCode
   * @param {Array} scannedItems
   * @param {string} timeOfDay
   */
  async getPersonalized(employeeCode, scannedItems = null, timeOfDay = 'lunch') {
    const res = await fetch(`${API_BASE}/recommendations/personalized-meal`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        employee_code: employeeCode,
        scanned_items: scannedItems,
        time_of_day: timeOfDay,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to fetch personalized recommendations');
    }
    return await res.json();
  },

  async getSuggestions(employeeCode, timeOfDay = 'lunch') {
    const res = await fetch(`${API_BASE}/recommendations/suggestions/${employeeCode}?time_of_day=${timeOfDay}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to fetch suggestions');
    }
    return await res.json();
  }
};

