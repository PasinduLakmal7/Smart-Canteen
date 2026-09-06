import React from 'react';
import { Flame, CheckCircle, AlertTriangle } from 'lucide-react';

export default function CalorieGauge({ mealCalories, dailyTarget = 2200 }) {
  if (!mealCalories || mealCalories === 0) return null;

  const percentage = Math.min(Math.round((mealCalories / dailyTarget) * 100), 100);
  
  let statusColor = 'var(--accent-emerald)';
  let statusText = 'Optimal Calorie Ratio';
  if (percentage > 50 && percentage <= 75) {
    statusColor = 'var(--accent-amber)';
    statusText = 'Substantial Meal';
  } else if (percentage > 75) {
    statusColor = 'var(--accent-rose)';
    statusText = 'High Calorie Density';
  }

  return (
    <div className="calorie-gauge-card">
      <div className="gauge-header">
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-main)' }}>
          <Flame size={16} className="text-orange" />
          Meal Calorie Impact
        </span>
        <span style={{ color: statusColor, fontWeight: 700 }}>
          {percentage}% of Daily Target ({mealCalories.toFixed(0)} / {dailyTarget} kcal)
        </span>
      </div>

      <div className="progress-bar-bg">
        <div 
          className="progress-bar-fill" 
          style={{ width: `${percentage}%` }}
        />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.4rem' }}>
        <span>0 kcal</span>
        <span style={{ color: statusColor, fontWeight: 700 }}>{statusText}</span>
        <span>{dailyTarget} kcal target</span>
      </div>
    </div>
  );
}
