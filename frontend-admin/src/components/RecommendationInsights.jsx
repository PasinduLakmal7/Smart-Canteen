import React, { useState, useEffect, useMemo } from 'react';
import { 
  Sparkles, 
  User, 
  Flame, 
  TrendingUp, 
  ShieldAlert, 
  ShieldCheck, 
  HeartHandshake, 
  Utensils, 
  CheckCircle, 
  Clock, 
  Layers, 
  Activity,
  PlusCircle,
  RefreshCw,
  Search,
  Award,
  Zap,
  Info
} from 'lucide-react';
import { employeeApi, recommendationApi, foodsApi } from '../services/api';

export default function RecommendationInsights({ employees = [], onRefresh }) {
  const [selectedEmpCode, setSelectedEmpCode] = useState('');
  const [employeeProfile, setEmployeeProfile] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [timeOfDay, setTimeOfDay] = useState('lunch');
  const [availableFoods, setAvailableFoods] = useState([]);
  const [simulatedPlate, setSimulatedPlate] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Initial employee selection
  useEffect(() => {
    if (employees.length > 0 && !selectedEmpCode) {
      setSelectedEmpCode(employees[0].employee_id);
    }
  }, [employees, selectedEmpCode]);

  // Load foods catalog for simulation
  useEffect(() => {
    foodsApi.list()
      .then(data => setAvailableFoods(Array.isArray(data) ? data : []))
      .catch(err => console.error('Failed to load foods:', err));
  }, []);

  // Fetch employee profile & recommendations whenever employee or time-of-day changes
  const fetchRecommendations = async () => {
    if (!selectedEmpCode) return;
    setLoading(true);
    setError(null);
    try {
      // Fetch full profile
      const prof = await employeeApi.getProfile(selectedEmpCode).catch(() => null);
      setEmployeeProfile(prof);

      // Fetch personalized recommendations with current simulated plate
      const scannedNames = simulatedPlate.length > 0 ? simulatedPlate.map(f => f.food_name || f.name) : null;
      const recResult = await recommendationApi.getPersonalized(selectedEmpCode, scannedNames, timeOfDay);
      setRecommendations(recResult);
    } catch (err) {
      console.error('Failed to fetch recommendations:', err);
      setError(err.message || 'Failed to generate recommendation engine insights');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, [selectedEmpCode, timeOfDay, simulatedPlate]);

  const filteredEmployees = useMemo(() => {
    if (!searchTerm) return employees;
    const q = searchTerm.toLowerCase();
    return employees.filter(e => 
      e.name?.toLowerCase().includes(q) || 
      e.employee_id?.toLowerCase().includes(q) ||
      e.department?.toLowerCase().includes(q)
    );
  }, [employees, searchTerm]);

  const togglePlateItem = (food) => {
    const exists = simulatedPlate.some(f => (f.food_id || f.id) === (food.food_id || food.id));
    if (exists) {
      setSimulatedPlate(prev => prev.filter(f => (f.food_id || f.id) !== (food.food_id || food.id)));
    } else {
      setSimulatedPlate(prev => [...prev, food]);
    }
  };

  const getGoalColor = (goal) => {
    const g = (goal || '').toLowerCase();
    if (g.includes('muscle')) return 'var(--accent-purple)';
    if (g.includes('weight') || g.includes('loss')) return 'var(--accent-cyan)';
    if (g.includes('endurance') || g.includes('energy')) return 'var(--accent-orange)';
    return 'var(--accent-emerald)';
  };

  const budget = recommendations?.budget_status;
  const combos = recommendations?.combos || [];
  const addOns = recommendations?.plate_add_ons || [];
  const allergens = recommendations?.allergen_alerts || [];
  const safeAvailable = recommendations?.safe_available_foods || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Header & Overview Banner */}
      <div className="card" style={{ 
        background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.1) 0%, rgba(168, 85, 247, 0.12) 100%)',
        borderColor: 'rgba(6, 182, 212, 0.3)',
        padding: '1.5rem'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: 'var(--radius-md)',
              background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-purple))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: 'var(--shadow-glow-cyan)'
            }}>
              <Sparkles size={26} color="#ffffff" />
            </div>
            <div>
              <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-primary)', margin: 0, display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                Corporate Wellness & Personalized Nutrition Hub
                <span style={{ 
                  fontSize: '0.75rem', 
                  fontWeight: 700, 
                  color: 'var(--accent-emerald)', 
                  background: 'rgba(16, 185, 129, 0.15)', 
                  padding: '0.2rem 0.6rem', 
                  borderRadius: 'var(--radius-full)', 
                  border: '1px solid rgba(16, 185, 129, 0.3)' 
                }}>
                  Phase 6 AI Engine Active
                </span>
              </h2>
              <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                4-Pillar Algorithmic Optimizer: <strong style={{ color: 'var(--text-secondary)' }}>User Profile</strong> + <strong style={{ color: 'var(--text-secondary)' }}>Meal History</strong> + <strong style={{ color: 'var(--text-secondary)' }}>Live Plate Nutrition</strong> + <strong style={{ color: 'var(--text-secondary)' }}>Canteen Inventory</strong>
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <div style={{ display: 'flex', background: 'var(--bg-card-inner)', borderRadius: 'var(--radius-sm)', padding: '0.25rem', border: '1px solid var(--border-subtle)' }}>
              {['breakfast', 'lunch', 'dinner', 'snack'].map((period) => (
                <button
                  key={period}
                  onClick={() => setTimeOfDay(period)}
                  style={{
                    padding: '0.4rem 0.75rem',
                    border: 'none',
                    borderRadius: 'var(--radius-xs)',
                    background: timeOfDay === period ? 'var(--accent-cyan)' : 'transparent',
                    color: timeOfDay === period ? '#000000' : 'var(--text-muted)',
                    fontWeight: timeOfDay === period ? 700 : 500,
                    fontSize: '0.8rem',
                    cursor: 'pointer',
                    textTransform: 'capitalize',
                    transition: 'all 0.2s ease'
                  }}
                >
                  {period}
                </button>
              ))}
            </div>

            <button 
              className="btn btn-outline" 
              onClick={fetchRecommendations}
              disabled={loading}
              style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 0.9rem' }}
            >
              <RefreshCw size={14} className={loading ? 'spin' : ''} />
              <span>Recalculate</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Grid: Left Controls (Profile & Simulator) / Right Results (Combos & Health Nudge) */}
      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '1.5rem', alignItems: 'start' }}>
        
        {/* Left Column: Employee Selector & Interactive Plate Simulator */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          
          {/* Employee Picker Card */}
          <div className="card" style={{ padding: '1.25rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <User size={16} style={{ color: 'var(--accent-cyan)' }} />
              <span>Select Employee Profile</span>
            </h3>

            {/* Search filter */}
            <div style={{ position: 'relative', marginBottom: '0.75rem' }}>
              <Search size={14} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
              <input
                type="text"
                className="input-field"
                placeholder="Search employee..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ paddingLeft: '2.25rem', width: '100%', fontSize: '0.85rem' }}
              />
            </div>

            {/* Employee Dropdown / List */}
            <div style={{ maxHeight: '180px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.35rem', paddingRight: '0.25rem' }}>
              {filteredEmployees.map(emp => {
                const isSelected = selectedEmpCode === emp.employee_id;
                return (
                  <button
                    key={emp.employee_id}
                    onClick={() => setSelectedEmpCode(emp.employee_id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '0.55rem 0.75rem',
                      borderRadius: 'var(--radius-xs)',
                      background: isSelected ? 'rgba(6, 182, 212, 0.18)' : 'var(--bg-card-inner)',
                      border: `1px solid ${isSelected ? 'var(--accent-cyan)' : 'var(--border-subtle)'}`,
                      color: 'var(--text-primary)',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{emp.name}</div>
                      <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>{emp.employee_id} • {emp.department || 'Staff'}</div>
                    </div>
                    {isSelected && <CheckCircle size={14} style={{ color: 'var(--accent-cyan)' }} />}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Active Employee Health Attributes Card */}
          {employeeProfile && (
            <div className="card" style={{ padding: '1.25rem', background: 'var(--bg-card)' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Activity size={16} style={{ color: 'var(--accent-purple)' }} />
                <span>Health & Diet Profile</span>
              </h3>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.65rem' }}>
                <div style={{ background: 'var(--bg-card-inner)', padding: '0.65rem', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Health Goal</div>
                  <div style={{ 
                    fontSize: '0.85rem', 
                    fontWeight: 700, 
                    color: getGoalColor(employeeProfile.health_goal),
                    marginTop: '0.2rem'
                  }}>
                    {employeeProfile.health_goal ? employeeProfile.health_goal.replace(/_/g, ' ') : 'General Wellness'}
                  </div>
                </div>

                <div style={{ background: 'var(--bg-card-inner)', padding: '0.65rem', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Diet Style</div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.2rem' }}>
                    {employeeProfile.diet_type || 'Standard'}
                  </div>
                </div>

                <div style={{ background: 'var(--bg-card-inner)', padding: '0.65rem', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Daily Calorie Goal</div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent-orange)', marginTop: '0.2rem' }}>
                    {employeeProfile.daily_calorie_target ? `${employeeProfile.daily_calorie_target} kcal` : '2,000 kcal'}
                  </div>
                </div>

                <div style={{ background: 'var(--bg-card-inner)', padding: '0.65rem', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>BMI / Category</div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.2rem' }}>
                    {employeeProfile.bmi ? `${employeeProfile.bmi} (${employeeProfile.bmi_category || 'Normal'})` : '22.4 (Normal)'}
                  </div>
                </div>
              </div>

              {/* Allergies / Intolerances */}
              {employeeProfile.allergies && employeeProfile.allergies.length > 0 && (
                <div style={{ marginTop: '0.85rem' }}>
                  <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>Strict Allergen Restrictions:</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                    {employeeProfile.allergies.map((alg, idx) => (
                      <span key={idx} style={{
                        fontSize: '0.725rem',
                        fontWeight: 600,
                        background: 'rgba(244, 63, 94, 0.18)',
                        color: 'var(--accent-rose)',
                        border: '1px solid rgba(244, 63, 94, 0.35)',
                        padding: '0.15rem 0.5rem',
                        borderRadius: 'var(--radius-full)'
                      }}>
                        🚫 {alg}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Interactive Live Plate Simulator */}
          <div className="card" style={{ padding: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Utensils size={16} style={{ color: 'var(--accent-emerald)' }} />
                <span>Simulate Scanned Plate</span>
              </h3>
              {simulatedPlate.length > 0 && (
                <button 
                  onClick={() => setSimulatedPlate([])}
                  style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '0.75rem', cursor: 'pointer', textDecoration: 'underline' }}
                >
                  Clear Plate ({simulatedPlate.length})
                </button>
              )}
            </div>

            <p style={{ fontSize: '0.775rem', color: 'var(--text-muted)', margin: '0 0 0.75rem 0' }}>
              Toggle items below to simulate food placed on the camera tray:
            </p>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', maxHeight: '160px', overflowY: 'auto' }}>
              {availableFoods.map(food => {
                const isSelected = simulatedPlate.some(f => (f.food_id || f.id) === (food.food_id || food.id));
                return (
                  <button
                    key={food.food_id || food.id}
                    onClick={() => togglePlateItem(food)}
                    style={{
                      padding: '0.3rem 0.6rem',
                      borderRadius: 'var(--radius-full)',
                      border: `1px solid ${isSelected ? 'var(--accent-emerald)' : 'var(--border-subtle)'}`,
                      background: isSelected ? 'rgba(16, 185, 129, 0.2)' : 'var(--bg-card-inner)',
                      color: isSelected ? 'var(--accent-emerald)' : 'var(--text-secondary)',
                      fontSize: '0.75rem',
                      fontWeight: isSelected ? 700 : 500,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.3rem',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <span>{isSelected ? '✓' : '+'}</span>
                    <span>{food.food_name || food.name}</span>
                  </button>
                );
              })}
            </div>
          </div>

        </div>

        {/* Right Column: AI Output (Health Nudge, Calorie Budget, Curated Combos, Add-ons) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          
          {/* Motivational Health Nudge */}
          {recommendations?.health_nudge && (
            <div className="card" style={{ 
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(6, 182, 212, 0.08) 100%)',
              borderColor: 'rgba(16, 185, 129, 0.35)',
              padding: '1.25rem',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '1rem'
            }}>
              <div style={{
                width: '38px',
                height: '38px',
                borderRadius: 'var(--radius-sm)',
                background: 'rgba(16, 185, 129, 0.2)',
                border: '1px solid rgba(16, 185, 129, 0.4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}>
                <HeartHandshake size={20} style={{ color: 'var(--accent-emerald)' }} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-emerald)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  AI Wellness Coach Insight
                </div>
                <div style={{ fontSize: '0.925rem', color: 'var(--text-primary)', marginTop: '0.2rem', lineHeight: '1.45', fontWeight: 500 }}>
                  "{recommendations.health_nudge}"
                </div>
              </div>
            </div>
          )}

          {/* Allergen Alerts Warning Banner */}
          {allergens.length > 0 && (
            <div className="card" style={{
              background: 'rgba(244, 63, 94, 0.12)',
              borderColor: 'rgba(244, 63, 94, 0.4)',
              padding: '1rem 1.25rem'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <ShieldAlert size={22} style={{ color: 'var(--accent-rose)' }} />
                <div>
                  <div style={{ fontWeight: 700, color: 'var(--accent-rose)', fontSize: '0.9rem' }}>
                    Active Dietary / Allergen Warning
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-primary)', marginTop: '0.2rem' }}>
                    {allergens.join(' • ')}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Calorie & Macro Budget Tracker */}
          {budget && (
            <div className="card" style={{ padding: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem' }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Flame size={18} style={{ color: 'var(--accent-orange)' }} />
                  <span>Today's Nutritional Budget</span>
                </h3>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Daily Target: <strong style={{ color: 'var(--text-primary)' }}>{budget.daily_target_calories} kcal</strong>
                </span>
              </div>

              {/* Progress Bar */}
              <div style={{ marginBottom: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.35rem' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>
                    Consumed: <strong>{budget.consumed_calories_today} kcal</strong> ({Math.round(budget.percentage_used || 0)}%)
                  </span>
                  <span style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>
                    Remaining: {budget.remaining_calories} kcal
                  </span>
                </div>
                <div style={{
                  height: '10px',
                  background: 'var(--bg-card-inner)',
                  borderRadius: 'var(--radius-full)',
                  overflow: 'hidden',
                  border: '1px solid var(--border-subtle)',
                  position: 'relative'
                }}>
                  <div style={{
                    width: `${Math.min(budget.percentage_used || 0, 100)}%`,
                    height: '100%',
                    background: (budget.percentage_used || 0) > 90 
                      ? 'var(--accent-rose)' 
                      : 'linear-gradient(90deg, var(--accent-cyan), var(--accent-emerald))',
                    borderRadius: 'var(--radius-full)',
                    transition: 'width 0.4s ease'
                  }} />
                </div>
              </div>

              {/* Macro Pills */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem' }}>
                <div style={{ background: 'var(--bg-card-inner)', padding: '0.65rem', borderRadius: 'var(--radius-xs)', textAlign: 'center', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Consumed Cal</div>
                  <div style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--accent-orange)', marginTop: '0.15rem' }}>
                    {budget.consumed_calories_today}
                  </div>
                </div>

                <div style={{ background: 'var(--bg-card-inner)', padding: '0.65rem', borderRadius: 'var(--radius-xs)', textAlign: 'center', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Protein Today</div>
                  <div style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--accent-purple)', marginTop: '0.15rem' }}>
                    {budget.consumed_protein_today || 0}g
                  </div>
                </div>

                <div style={{ background: 'var(--bg-card-inner)', padding: '0.65rem', borderRadius: 'var(--radius-xs)', textAlign: 'center', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Carbs Today</div>
                  <div style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--accent-cyan)', marginTop: '0.15rem' }}>
                    {budget.consumed_carbs_today || 0}g
                  </div>
                </div>

                <div style={{ background: 'var(--bg-card-inner)', padding: '0.65rem', borderRadius: 'var(--radius-xs)', textAlign: 'center', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Allowance Left</div>
                  <div style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--accent-emerald)', marginTop: '0.15rem' }}>
                    {budget.remaining_calories} kcal
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Smart Plate Add-on Suggestions (if plate is simulated or low macros detected) */}
          {addOns.length > 0 && (
            <div className="card" style={{ padding: '1.25rem', borderColor: 'rgba(168, 85, 247, 0.3)' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <PlusCircle size={16} style={{ color: 'var(--accent-purple)' }} />
                <span>Plate Optimization Add-ons & Deficit Solvers</span>
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '0.75rem' }}>
                {addOns.map((addon, idx) => (
                  <div key={idx} style={{
                    background: 'var(--bg-card-inner)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '0.75rem'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div style={{ fontWeight: 700, fontSize: '0.875rem', color: 'var(--text-primary)' }}>
                        + {addon.food_name}
                      </div>
                      <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                        Rs. {addon.price_lkr}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--accent-purple)', fontWeight: 600, marginTop: '0.2rem' }}>
                      {addon.reason}
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.4rem', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      <span>{addon.calories} kcal</span>
                      <span>•</span>
                      <span>{addon.protein}g Protein</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommended Goal-Aligned Meal Combos */}
          <div className="card" style={{ padding: '1.25rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Award size={18} style={{ color: 'var(--accent-cyan)' }} />
              <span>Recommended Curated Meal Combos ({combos.length})</span>
            </h3>

            {loading ? (
              <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                <RefreshCw size={24} className="spin" style={{ margin: '0 auto 0.75rem auto' }} />
                <div>Computing optimal nutrition combinations...</div>
              </div>
            ) : combos.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                No combos found matching exact profile restrictions.
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
                {combos.map((combo, idx) => (
                  <div 
                    key={combo.combo_id || idx}
                    style={{
                      background: 'var(--bg-card-inner)',
                      borderRadius: 'var(--radius-md)',
                      border: idx === 0 ? '1.5px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                      padding: '1.1rem',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      position: 'relative',
                      overflow: 'hidden'
                    }}
                  >
                    {idx === 0 && (
                      <div style={{
                        position: 'absolute',
                        top: 0,
                        right: 0,
                        background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-purple))',
                        color: '#ffffff',
                        fontSize: '0.675rem',
                        fontWeight: 800,
                        padding: '0.2rem 0.6rem',
                        borderBottomLeftRadius: 'var(--radius-xs)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.04em'
                      }}>
                        Top Match
                      </div>
                    )}

                    <div>
                      <div style={{ fontWeight: 800, fontSize: '0.975rem', color: 'var(--text-primary)', marginBottom: '0.25rem', paddingRight: '4rem' }}>
                        {combo.name}
                      </div>

                      <div style={{ fontSize: '0.75rem', color: 'var(--accent-emerald)', fontWeight: 600, marginBottom: '0.65rem' }}>
                        {combo.reason_for_recommendation}
                      </div>

                      {/* Items list */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem', marginBottom: '0.85rem' }}>
                        {combo.items.map((item, iIdx) => (
                          <div key={iIdx} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.775rem', color: 'var(--text-secondary)' }}>
                            <span>• {item.food_name}</span>
                            <span style={{ color: 'var(--text-muted)' }}>{item.portion_desc || `${item.calories} kcal`}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Bottom Macros & Price bar */}
                    <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '0.75rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          <strong style={{ color: 'var(--accent-orange)' }}>{combo.total_calories} kcal</strong> • <strong style={{ color: 'var(--accent-purple)' }}>{combo.total_protein}g P</strong> • <span style={{ color: 'var(--accent-cyan)' }}>{combo.total_carbs}g C</span>
                        </div>
                        <div style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>
                          Rs. {combo.total_price_lkr}
                        </div>
                      </div>

                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                        <span>Match Score: {combo.health_match_score}%</span>
                        <span>{combo.health_goal_alignment ? combo.health_goal_alignment.replace(/_/g, ' ') : 'Aligned'}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>

      </div>
    </div>
  );
}
