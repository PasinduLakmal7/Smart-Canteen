/**
 * Smart Canteen AI — Executive Admin & HR Portal API Client
 * Manages Employee CRUD, 128D Face Biometrics, Nutrition Profiles, Menu Pricing, and Transactions
 */

const API_BASE = '/api/v1';

function formatErrorDetail(err, defaultMsg = 'Request failed') {
  if (!err) return defaultMsg;
  if (typeof err.detail === 'string') return err.detail;
  if (Array.isArray(err.detail)) {
    return err.detail.map((d) => (d.msg ? `${d.loc ? d.loc.slice(-1)[0] + ': ' : ''}${d.msg}` : JSON.stringify(d))).join(', ');
  }
  if (err.message) return err.message;
  return defaultMsg;
}

export const employeeApi = {
  async list() {
    const res = await fetch(`${API_BASE}/employees`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(formatErrorDetail(err, 'Failed to fetch employees list'));
    }
    const data = await res.json();
    return data.employees || [];
  },

  async create(data) {
    const res = await fetch(`${API_BASE}/employees`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(formatErrorDetail(err, 'Failed to create employee'));
    }
    const result = await res.json();
    return result.employee || result;
  },

  async getProfile(idOrCode) {
    const res = await fetch(`${API_BASE}/employees/${idOrCode}/full-profile`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(formatErrorDetail(err, `Failed to fetch profile for ${idOrCode}`));
    }
    const data = await res.json();
    return data.data || data;
  },

  async createProfile(employeeId, data) {
    const res = await fetch(`${API_BASE}/employees/${employeeId}/profile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(formatErrorDetail(err, 'Failed to create employee profile'));
    }
    return res.json();
  },

  async updateProfile(employeeId, data) {
    const res = await fetch(`${API_BASE}/employees/${employeeId}/profile`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(formatErrorDetail(err, 'Failed to update employee profile'));
    }
    return res.json();
  }
};

export const faceApi = {
  async register(formData) {
    const res = await fetch(`${API_BASE}/face/register`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(formatErrorDetail(err, 'Face registration failed'));
    }
    const data = await res.json();
    return data.data || data;
  },

  async listEnrolled() {
    const res = await fetch(`${API_BASE}/face/enrolled`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(formatErrorDetail(err, 'Failed to fetch enrolled faces'));
    }
    const data = await res.json();
    return data.enrolled_employees || [];
  },

  async deactivate(empCode) {
    const res = await fetch(`${API_BASE}/face/${empCode}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(formatErrorDetail(err, `Failed to deactivate face for ${empCode}`));
    }
    return res.json();
  },

  async evaluate(threshold = 0.6) {
    const res = await fetch(`${API_BASE}/face/evaluate?threshold=${threshold}`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(formatErrorDetail(err, 'Failed to run benchmark evaluation'));
    }
    const data = await res.json();
    return data.data || data;
  }
};

export const foodsApi = {
  async list() {
    const res = await fetch(`${API_BASE}/foods`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(formatErrorDetail(err, 'Failed to fetch food catalog'));
    }
    const data = await res.json();
    return data.foods || [];
  },

  async updatePrice(foodId, priceLkr) {
    const res = await fetch(`${API_BASE}/admin/foods/${foodId}/price`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ price: priceLkr }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(formatErrorDetail(err, 'Failed to update food price'));
    }
    return res.json();
  }
};

export const transactionApi = {
  async list(filters = {}) {
    const params = new URLSearchParams();
    if (filters.employee_id) params.append('employee_id', filters.employee_id);
    if (filters.date) params.append('date', filters.date);
    if (filters.department) params.append('department', filters.department);
    if (filters.payment_status) params.append('payment_status', filters.payment_status);
    if (filters.limit) params.append('limit', filters.limit);

    const query = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`${API_BASE}/meal-transactions${query}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(formatErrorDetail(err, 'Failed to fetch transactions'));
    }
    const data = await res.json();
    return data.transactions || [];
  },

  async get(idOrCode) {
    const res = await fetch(`${API_BASE}/meal-transactions/${idOrCode}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(formatErrorDetail(err, `Failed to fetch transaction ${idOrCode}`));
    }
    const data = await res.json();
    return data.transaction || data;
  },

  async getAnalytics() {
    const res = await fetch(`${API_BASE}/analytics/canteen-summary`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(formatErrorDetail(err, 'Failed to fetch canteen analytics'));
    }
    const data = await res.json();
    return data.analytics || data;
  }
};

export const recommendationApi = {
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
      throw new Error(formatErrorDetail(err, 'Failed to fetch recommendations'));
    }
    return await res.json();
  },

  async getSuggestions(employeeCode, timeOfDay = 'lunch') {
    const res = await fetch(`${API_BASE}/recommendations/suggestions/${employeeCode}?time_of_day=${timeOfDay}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(formatErrorDetail(err, 'Failed to fetch suggestions'));
    }
    return await res.json();
  }
};

