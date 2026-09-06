import React, { useState, useEffect } from 'react';
import { X, History, Calendar, Flame, DollarSign, Utensils, RefreshCw, CheckCircle2 } from 'lucide-react';
import { transactionApi } from '../services/api';

export default function MealHistoryModal({ isOpen, onClose, employeeCode, employeeName }) {
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchHistory = async () => {
    if (!employeeCode) return;
    setLoading(true);
    setError(null);
    try {
      const res = await transactionApi.getHistory(employeeCode);
      setHistory(res);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to load meal history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && employeeCode) {
      fetchHistory();
    }
  }, [isOpen, employeeCode]);

  if (!isOpen) return null;

  const meals = history?.meals || [];
  const totalMeals = history?.total_meals || 0;
  const totalCals = history?.total_calories || 0;
  const totalSpent = history?.formatted_total_spent || `Rs. ${(history?.total_spent_lkr || 0).toFixed(2)}`;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: '680px', maxHeight: '85vh', display: 'flex', flexDirection: 'column', textAlign: 'left' }} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '1rem', borderBottom: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <History className="text-cyan" size={24} />
            <div>
              <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.25rem', color: 'var(--text-main)', fontWeight: 800 }}>Personal Meal History</h3>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                {employeeName} ({employeeCode})
              </div>
            </div>
          </div>
          <button className="btn btn-outline" style={{ padding: '0.3rem 0.6rem' }} onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        {/* Top Summary Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', margin: '1.25rem 0' }}>
          <div style={{ background: 'var(--tile-bg)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>Total Meals</div>
            <div style={{ fontFamily: 'var(--font-heading)', fontSize: '1.3rem', fontWeight: 800, color: 'var(--text-main)' }}>{totalMeals}</div>
          </div>
          <div style={{ background: 'var(--tile-bg)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>Total Energy</div>
            <div style={{ fontFamily: 'var(--font-heading)', fontSize: '1.3rem', fontWeight: 800, color: 'var(--accent-orange)' }}>{totalCals.toFixed(0)} kcal</div>
          </div>
          <div style={{ background: 'var(--tile-bg)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>Payroll Billed</div>
            <div style={{ fontFamily: 'var(--font-heading)', fontSize: '1.3rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>{totalSpent}</div>
          </div>
        </div>

        {/* Body List */}
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.75rem', paddingRight: '0.25rem' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
              <RefreshCw className="spin text-cyan" size={24} style={{ margin: '0 auto 0.5rem auto' }} />
              <div>Loading meal history...</div>
            </div>
          ) : error ? (
            <div style={{ background: 'rgba(244,63,94,0.12)', color: 'var(--accent-rose)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(244,63,94,0.25)' }}>
              ⚠️ {error}
            </div>
          ) : meals.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2.5rem 1rem', color: 'var(--text-muted)' }}>
              <Utensils size={36} style={{ opacity: 0.35, margin: '0 auto 0.5rem auto' }} />
              <div style={{ color: 'var(--text-main)', fontWeight: 600 }}>No meal transactions recorded yet</div>
              <div style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>Your canteen orders and payroll charges will appear here.</div>
            </div>
          ) : (
            meals.map((meal, idx) => (
              <div 
                key={meal.transaction_id || idx}
                style={{
                  background: 'var(--bg-card-inner)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '1rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                      {meal.transaction_code}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>•</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {meal.date} • {meal.time}
                    </span>
                  </div>
                  <div style={{ fontWeight: 700, color: 'var(--text-main)', fontSize: '0.95rem' }}>
                    {meal.foods.length > 0 ? meal.foods.join(', ') : 'Canteen Meal'}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                    Protein: {meal.macros?.protein_g || 0}g • Carbs: {meal.macros?.carbs_g || 0}g • Fat: {meal.macros?.fat_g || 0}g
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontFamily: 'var(--font-heading)', fontWeight: 800, fontSize: '1.1rem', color: 'var(--text-main)' }}>
                    {meal.formatted_amount}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--accent-orange)', fontWeight: 700 }}>
                    {meal.calories.toFixed(0)} kcal
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div style={{ marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border-subtle)', textAlign: 'right' }}>
          <button className="btn btn-primary" style={{ width: 'auto', padding: '0.5rem 1.25rem' }} onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
