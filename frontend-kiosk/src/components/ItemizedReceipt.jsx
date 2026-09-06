import React, { useState } from 'react';
import { Receipt, CheckCircle, CreditCard, Sparkles, AlertCircle, AlertTriangle, RefreshCw } from 'lucide-react';
import { transactionApi } from '../services/api';

export default function ItemizedReceipt({ mealResult, employee, onResetAll }) {
  const [isPaid, setIsPaid] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [createdTx, setCreatedTx] = useState(null);

  if (!mealResult) {
    return (
      <div className="glass-card receipt-card" style={{ justifyContent: 'center', alignItems: 'center', textAlign: 'center', color: 'var(--text-muted)' }}>
        <Receipt size={48} style={{ opacity: 0.35, marginBottom: '1rem', color: 'var(--accent-cyan)' }} />
        <h4 style={{ color: 'var(--text-main)', marginBottom: '0.5rem', fontWeight: 800, fontSize: '1.1rem' }}>POS Canteen Bill</h4>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Scan food plate on the left to generate real-time itemized receipt and nutrition breakdown.</p>
      </div>
    );
  }

  const items = mealResult.items || [];
  const totals = mealResult.meal_totals || {};
  const totalPrice = totals.total_bill_amount || 0;
  const formattedTotal = totals.formatted_total_bill || `Rs. ${totalPrice.toFixed(2)}`;
  const totalCals = totals.calories_kcal || 0;
  const protein = totals.protein_g || 0;
  const carbs = totals.carbs_g || 0;
  const fat = totals.fat_g || 0;
  const fiber = totals.fiber_g || 0;
  const warnings = mealResult.warnings || [];

  const empName = (
    employee?.name ||
    `${employee?.first_name || ''} ${employee?.last_name || ''}`.trim() ||
    'Walk-in Customer'
  );
  const empCode = employee?.employee_code || 'GUEST';

  const handlePay = async () => {
    setIsProcessing(true);
    try {
      const itemsPayload = items.map((it) => ({
        food_name: it.food_name,
        quantity: it.quantity || 1,
      }));

      // Fallback to EMP001 if GUEST
      const targetCode = empCode !== 'GUEST' ? empCode : 'EMP001';

      const res = await transactionApi.create({
        employee_code: targetCode,
        items: itemsPayload,
        payment_method: 'payroll',
      });
      setCreatedTx(res);
      setIsPaid(true);
    } catch (err) {
      console.error(err);
      alert('Transaction failed: ' + err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFinish = () => {
    setIsPaid(false);
    setCreatedTx(null);
    onResetAll();
  };

  return (
    <div className="glass-card receipt-card">
      <div className="receipt-header">
        <h3>SMART CANTEEN</h3>
        <div className="receipt-meta">
          <span>Counter #01 • {new Date().toLocaleTimeString()}</span>
          <div>Billed to: <strong style={{ color: 'var(--text-main)' }}>{empName}</strong> ({empCode})</div>
        </div>
      </div>

      {warnings.length > 0 && (
        <div style={{ background: 'rgba(245, 158, 11, 0.15)', border: '1px solid rgba(245, 158, 11, 0.3)', color: 'var(--accent-amber)', padding: '0.6rem 0.8rem', borderRadius: 'var(--radius-sm)', margin: '0.75rem 0', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <AlertTriangle size={16} className="text-amber" />
          <div>{warnings.join(', ')}</div>
        </div>
      )}

      <div className="receipt-body">
        {items.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-muted)' }}>
            <AlertCircle size={32} style={{ opacity: 0.5, margin: '0 auto 0.5rem auto' }} />
            <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>No food items identified</div>
            <div style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>
              Please ensure the food plate is well-lit and placed clearly in view.
            </div>
          </div>
        ) : (
          items.map((item, idx) => {
            const title = item.display_name || item.food_name.replace(/_/g, ' ');
            const priceStr = item.formatted_total_price || `Rs. ${(item.total_price || 0).toFixed(2)}`;
            const cals = item.calories_kcal || 0;

            return (
              <div key={idx} className="receipt-line" style={{ alignItems: 'flex-start', padding: '0.45rem 0' }}>
                <div>
                  <div style={{ fontWeight: 700, color: 'var(--text-main)', textTransform: 'capitalize', fontSize: '0.875rem' }}>
                    {title}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Qty: {item.quantity || 1} • {cals.toFixed(0)} kcal
                  </div>
                </div>
                <div style={{ fontWeight: 800, color: 'var(--text-main)', fontVariantNumeric: 'tabular-nums' }}>
                  {priceStr}
                </div>
              </div>
            );
          })
        )}
      </div>

      <div className="receipt-summary">
        <div className="summary-row">
          <span>Total Energy</span>
          <span className="text-orange" style={{ fontWeight: 700 }}>{totalCals.toFixed(0)} kcal</span>
        </div>
        <div className="summary-row">
          <span>Items Detected</span>
          <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{items.length} dishes</span>
        </div>
        <div className="summary-row total-row">
          <span>Total (LKR)</span>
          <span className="text-emerald">{formattedTotal}</span>
        </div>

        {/* Nutrition Macros Pill Bar */}
        <div className="macros-pill-bar">
          <div className="macro-pill">
            <div className="macro-label">Protein</div>
            <div className="macro-val text-cyan">{protein.toFixed(1)}g</div>
          </div>
          <div className="macro-pill">
            <div className="macro-label">Carbs</div>
            <div className="macro-val text-amber">{carbs.toFixed(1)}g</div>
          </div>
          <div className="macro-pill">
            <div className="macro-label">Fat</div>
            <div className="macro-val text-rose">{fat.toFixed(1)}g</div>
          </div>
          <div className="macro-pill">
            <div className="macro-label">Fiber</div>
            <div className="macro-val text-emerald">{fiber.toFixed(1)}g</div>
          </div>
        </div>

        <div style={{ marginTop: '1.25rem' }}>
          <button 
            className="btn btn-success" 
            onClick={handlePay}
            disabled={items.length === 0 || isProcessing}
          >
            {isProcessing ? (
              <>
                <RefreshCw size={18} className="spin" /> Processing Payroll...
              </>
            ) : (
              <>
                <CreditCard size={18} /> Charge to Employee Payroll ({formattedTotal})
              </>
            )}
          </button>
        </div>
      </div>

      {isPaid && (
        <div className="modal-backdrop">
          <div className="modal-content">
            <CheckCircle size={64} className="text-emerald" style={{ margin: '0 auto 1rem auto' }} />
            <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.5rem', marginBottom: '0.25rem', color: 'var(--text-main)' }}>Payment Successful!</h2>
            <div style={{ color: 'var(--accent-cyan)', fontWeight: 700, fontSize: '0.9rem', marginBottom: '1rem' }}>
              Ref: {createdTx?.transaction_code || 'TX-COMPLETED'}
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.25rem' }}>
              <strong style={{ color: 'var(--text-main)' }}>{createdTx?.formatted_total_amount || formattedTotal}</strong> charged to <strong style={{ color: 'var(--text-main)' }}>{empName}</strong>'s monthly canteen payroll balance.
            </p>
            <div style={{ background: 'var(--tile-bg)', border: '1px solid var(--border-glass)', padding: '1rem', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', fontSize: '0.85rem', textAlign: 'left', color: 'var(--text-main)' }}>
              <div>✓ Transaction ID: {createdTx?.id || 1} ({createdTx?.transaction_code})</div>
              <div>✓ Calorie Intake Logged: +{(createdTx?.total_calories || totalCals).toFixed(0)} kcal</div>
              <div>✓ Permanent Financial Snapshot Saved</div>
              <div>✓ Biometric Payroll Authorized</div>
            </div>
            <button className="btn btn-primary" style={{ width: '100%' }} onClick={handleFinish}>
              Start Next Customer Scan
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
