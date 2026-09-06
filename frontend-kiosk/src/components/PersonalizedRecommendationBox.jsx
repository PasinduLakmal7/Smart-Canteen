import React from 'react';
import { 
  Sparkles, Flame, PlusCircle, CheckCircle2, AlertTriangle, 
  TrendingUp, Award, ShieldCheck, Heart, ArrowRight, Zap, Utensils
} from 'lucide-react';

export default function PersonalizedRecommendationBox({ recommendation, onSelectCombo }) {
  if (!recommendation) return null;

  const {
    employee_name,
    health_goal,
    bmi,
    bmi_category,
    budget_status,
    recommended_combos = [],
    smart_add_ons = [],
    warnings = [],
    health_nudge
  } = recommendation;

  const budget = budget_status || {};
  const remCals = budget.remaining_calories || 0;
  const targetCals = budget.daily_target_calories || 2200;
  const consumedCals = budget.today_consumed_calories || 0;
  const statusType = budget.budget_status || 'optimal';

  const formatGoal = (g = '') => {
    return g.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  };

  return (
    <div className="glass-card" style={{ marginTop: '1.25rem', padding: '1.25rem' }}>
      {/* Header with AI Badge & Health Goal */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.85rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Sparkles className="text-cyan" size={20} />
          <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 800, fontSize: '1rem', color: 'var(--text-main)' }}>
            AI Personalized Nutrition & Meal Advisor
          </span>
          <span className="badge badge-cyan" style={{ fontSize: '0.7rem' }}>Phase 6 Active</span>
        </div>

        <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
          <span className="badge badge-purple" style={{ fontSize: '0.725rem' }}>
            <Award size={11} /> Goal: {formatGoal(health_goal)}
          </span>
          <span className="badge badge-success" style={{ fontSize: '0.725rem' }}>
            BMI {bmi} ({bmi_category})
          </span>
        </div>
      </div>

      {/* Motivational Health Nudge Bubble */}
      {health_nudge && (
        <div 
          style={{ 
            background: 'var(--tile-bg)', 
            border: '1px solid var(--border-subtle)', 
            borderRadius: 'var(--radius-sm)', 
            padding: '0.75rem 1rem', 
            marginBottom: '1rem',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.65rem',
            fontSize: '0.825rem',
            color: 'var(--text-main)'
          }}
        >
          <Zap size={16} className="text-orange" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div style={{ lineHeight: 1.45 }}>
            <strong style={{ color: 'var(--accent-cyan)' }}>Smart Nudge:</strong> {health_nudge}
          </div>
        </div>
      )}

      {/* Warnings & Allergen Conflicts */}
      {warnings.length > 0 && (
        <div style={{ marginBottom: '1rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
          {warnings.map((w, i) => (
            <div 
              key={i}
              style={{ 
                background: 'rgba(244, 63, 94, 0.12)', 
                border: '1px solid rgba(244, 63, 94, 0.3)', 
                color: 'var(--accent-rose)', 
                padding: '0.6rem 0.85rem', 
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontWeight: 600
              }}
            >
              <AlertTriangle size={15} />
              <span>{w}</span>
            </div>
          ))}
        </div>
      )}

      {/* Daily Calorie Budget Tracker */}
      <div style={{ background: 'var(--bg-card-inner)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '0.85rem 1rem', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem', marginBottom: '0.4rem' }}>
          <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>Today's Calorie Budget</span>
          <span style={{ fontWeight: 800, color: statusType === 'exceeded' ? 'var(--accent-rose)' : statusType === 'approaching_limit' ? 'var(--accent-amber)' : 'var(--accent-emerald)' }}>
            {remCals.toFixed(0)} kcal remaining / {targetCals.toFixed(0)} kcal
          </span>
        </div>
        <div style={{ height: '6px', background: 'var(--tile-bg)', borderRadius: 'var(--radius-full)', overflow: 'hidden', border: '1px solid var(--border-subtle)' }}>
          <div 
            style={{ 
              height: '100%', 
              width: `${Math.min(Math.round((consumedCals / targetCals) * 100), 100)}%`, 
              background: statusType === 'exceeded' ? 'var(--accent-rose)' : 'linear-gradient(90deg, #10b981, #06b6d4)',
              borderRadius: 'var(--radius-full)'
            }} 
          />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '0.3rem' }}>
          <span>Consumed: {consumedCals.toFixed(0)} kcal</span>
          <span>Target: {targetCals.toFixed(0)} kcal</span>
        </div>
      </div>

      {/* Smart Plate Add-Ons (When Current Plate is Active) */}
      {smart_add_ons.length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ fontSize: '0.775rem', fontWeight: 800, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.5rem', letterSpacing: '0.04em' }}>
            🥗 Smart Plate Optimizations For This Meal
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '0.6rem' }}>
            {smart_add_ons.map((addon, idx) => (
              <div 
                key={idx}
                style={{ 
                  background: 'var(--tile-bg)', 
                  border: '1px solid var(--border-subtle)', 
                  borderRadius: 'var(--radius-sm)', 
                  padding: '0.65rem 0.85rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.65rem'
                }}
              >
                <div style={{ fontSize: '1.4rem' }}>{addon.item.emoji}</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 700, fontSize: '0.825rem', color: 'var(--text-main)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    + {addon.item.display_name} (Rs. {addon.item.price_lkr.toFixed(0)})
                  </div>
                  <div style={{ fontSize: '0.725rem', color: 'var(--accent-cyan)', marginTop: '1px' }}>
                    {addon.why_add}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommended Goal Combos */}
      <div>
        <div style={{ fontSize: '0.775rem', fontWeight: 800, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.6rem', letterSpacing: '0.04em' }}>
          🎯 Recommended Canteen Combos For You
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.75rem' }}>
          {recommended_combos.map((combo) => (
            <div 
              key={combo.combo_id}
              style={{ 
                background: 'var(--tile-bg)', 
                border: '1px solid var(--border-subtle)', 
                borderRadius: 'var(--radius-md)', 
                padding: '0.85rem 1rem',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: '0.6rem',
                transition: 'all 0.2s ease'
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                  <span style={{ fontWeight: 800, fontSize: '0.875rem', color: 'var(--text-main)' }}>
                    {combo.title}
                  </span>
                  <span className="badge badge-emerald" style={{ fontSize: '0.7rem', background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-emerald)', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                    {combo.match_score}% Match
                  </span>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem', lineHeight: 1.35 }}>
                  {combo.description}
                </div>

                {/* Items preview pills */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem', marginBottom: '0.5rem' }}>
                  {combo.items.map((it, i) => (
                    <span 
                      key={i}
                      style={{ 
                        background: 'var(--bg-card)', 
                        border: '1px solid var(--border-subtle)', 
                        padding: '0.15rem 0.45rem', 
                        borderRadius: 'var(--radius-xs)', 
                        fontSize: '0.725rem',
                        color: 'var(--text-main)',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.2rem'
                      }}
                    >
                      <span>{it.emoji}</span>
                      <span>{it.display_name}</span>
                    </span>
                  ))}
                </div>
              </div>

              {/* Nutrition & Price Footnote */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.5rem', fontSize: '0.775rem' }}>
                <div style={{ color: 'var(--accent-orange)', fontWeight: 700 }}>
                  <Flame size={12} style={{ display: 'inline', marginRight: '2px' }} />
                  {combo.total_calories.toFixed(0)} kcal • {combo.total_protein_g.toFixed(0)}g P
                </div>
                <div style={{ fontFamily: 'var(--font-heading)', fontWeight: 800, color: 'var(--accent-emerald)' }}>
                  {combo.formatted_total_price}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
