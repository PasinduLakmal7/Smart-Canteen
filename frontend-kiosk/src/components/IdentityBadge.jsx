import React from 'react';
import { UserCheck, ShieldAlert, Heart, Activity, History } from 'lucide-react';

export default function IdentityBadge({ employee, matchInfo, facePreviewUrl, onViewHistory }) {
  if (!employee && !matchInfo) {
    return (
      <div className="glass-card" style={{ padding: '1.25rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        <p style={{ fontSize: '0.9rem' }}>Scan employee face to identify profile and health goals.</p>
      </div>
    );
  }

  if (matchInfo && !matchInfo.matched) {
    return (
      <div className="glass-card" style={{ borderColor: 'rgba(244, 63, 94, 0.4)', background: 'rgba(244, 63, 94, 0.08)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#f43f5e' }}>
          <ShieldAlert size={24} />
          <div>
            <h4 style={{ fontWeight: 700, fontSize: '1rem', color: '#f43f5e' }}>Unknown Person Detected</h4>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Face does not match any enrolled active employee (T_match &lt; 0.60).</p>
          </div>
        </div>
      </div>
    );
  }

  const name = (
    employee?.name ||
    `${employee?.first_name || ''} ${employee?.last_name || ''}`.trim() ||
    matchInfo?.employee_name ||
    'Enrolled Employee'
  );
  const code = employee?.employee_code || matchInfo?.employee_code || 'EMP-UNKNOWN';
  const dept = employee?.department || 'Staff';
  const profile = employee?.profile || {};
  const bmi = profile?.bmi ? Number(profile.bmi).toFixed(1) : null;
  const bmiCategory = profile?.bmi_category || 'Healthy';
  const targetCals = profile?.daily_calorie_target || 2200;
  const restrictions = employee?.dietary_restrictions || profile?.dietary_restrictions || [];

  return (
    <div className="identity-card">
      <div className="avatar-container">
        {facePreviewUrl ? (
          <img src={facePreviewUrl} alt="Employee Avatar" className="avatar-img" />
        ) : (
          <UserCheck size={36} color="#fff" />
        )}
      </div>

      <div className="emp-info">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="emp-name">
            <span>{name}</span>
            <span className="emp-code-badge">{code}</span>
          </div>
          {onViewHistory && (
            <button
              className="btn btn-outline"
              style={{ padding: '0.3rem 0.65rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
              onClick={onViewHistory}
            >
              <History size={13} className="text-cyan" /> My Meal History
            </button>
          )}
        </div>

        <div className="emp-meta">
          <span>🏢 {dept}</span>
          {matchInfo?.confidence && (
            <span className="text-emerald" style={{ fontWeight: 600 }}>
              ✓ {(matchInfo.confidence * 100).toFixed(0)}% Match
            </span>
          )}
        </div>

        <div className="emp-tags">
          {bmi && (
            <span className="tag bmi-tag">
              <Activity size={12} style={{ display: 'inline', marginRight: '3px' }} />
              BMI {bmi} ({bmiCategory})
            </span>
          )}
          <span className="tag" style={{ background: 'rgba(6, 182, 212, 0.12)', color: 'var(--accent-cyan)', borderColor: 'rgba(6, 182, 212, 0.3)' }}>
            <Heart size={12} style={{ display: 'inline', marginRight: '3px' }} />
            Goal: {targetCals} kcal/day
          </span>
          {restrictions.map((r, i) => (
            <span key={i} className="tag diet-tag">
              ⚠️ {r}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
