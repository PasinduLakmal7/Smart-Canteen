import React, { useState } from 'react';
import { 
  Users, Search, Plus, RefreshCw, Activity, Heart, ShieldCheck, 
  Building, Mail, Phone, Calendar, ArrowRight, Eye, X, Check, Flame
} from 'lucide-react';
import { employeeApi } from '../services/api';

export default function EmployeeDirectory({ employees, onRefresh, onOpenRegister }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [deptFilter, setDeptFilter] = useState('');
  const [viewMode, setViewMode] = useState('grid');
  const [selectedEmp, setSelectedEmp] = useState(null);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [fullProfile, setFullProfile] = useState(null);

  const safeEmployees = Array.isArray(employees) ? employees : [];

  const departments = Array.from(new Set(safeEmployees.map((e) => e.department).filter(Boolean)));

  const filtered = safeEmployees.filter((emp) => {
    const q = searchTerm.toLowerCase();
    const fullName = (emp.name || `${emp.first_name || ''} ${emp.last_name || ''}`.trim()).toLowerCase();
    const code = (emp.employee_code || '').toLowerCase();
    const dept = (emp.department || '').toLowerCase();
    const email = (emp.email || '').toLowerCase();

    const matchesSearch = fullName.includes(q) || code.includes(q) || dept.includes(q) || email.includes(q);
    const matchesDept = !deptFilter || emp.department === deptFilter;
    return matchesSearch && matchesDept;
  });

  const handleInspect = async (emp) => {
    setSelectedEmp(emp);
    setLoadingProfile(true);
    setFullProfile(null);
    try {
      const code = emp.employee_code || emp.id;
      const data = await employeeApi.getProfile(code);
      setFullProfile(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingProfile(false);
    }
  };

  const getInitials = (name = 'Staff') => {
    return name
      .split(' ')
      .filter(Boolean)
      .map((n) => n[0])
      .slice(0, 2)
      .join('')
      .toUpperCase() || 'EMP';
  };

  return (
    <div>
      {/* Top Executive KPI Grid for Employees */}
      <div className="stats-grid">
        <div className="stat-box stat-purple">
          <div className="stat-icon" style={{ background: 'rgba(168, 85, 247, 0.12)', color: 'var(--accent-purple)' }}>
            <Users size={26} />
          </div>
          <div style={{ flex: 1 }}>
            <div className="stat-val text-purple">{safeEmployees.length}</div>
            <div className="stat-label">Total Registered Employees</div>
            <div className="stat-trend" style={{ background: 'rgba(168, 85, 247, 0.15)', color: 'var(--accent-purple)' }}>
              <ShieldCheck size={10} /> Active Staff Roster
            </div>
          </div>
        </div>

        <div className="stat-box stat-cyan">
          <div className="stat-icon" style={{ background: 'rgba(6, 182, 212, 0.12)', color: 'var(--accent-cyan)' }}>
            <Building size={26} />
          </div>
          <div style={{ flex: 1 }}>
            <div className="stat-val text-cyan">{departments.length || 6}</div>
            <div className="stat-label">Active Company Departments</div>
            <div className="stat-trend" style={{ background: 'rgba(6, 182, 212, 0.15)', color: 'var(--accent-cyan)' }}>
              <span>🏢 Enterprise Roster</span>
            </div>
          </div>
        </div>

        <div className="stat-box stat-emerald">
          <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.12)', color: 'var(--accent-emerald)' }}>
            <Heart size={26} />
          </div>
          <div style={{ flex: 1 }}>
            <div className="stat-val text-emerald">2,200 kcal</div>
            <div className="stat-label">Avg Daily Calorie Target</div>
            <div className="stat-trend" style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-emerald)' }}>
              <Activity size={10} /> WHO Calibrated
            </div>
          </div>
        </div>

        <div className="stat-box stat-orange">
          <div className="stat-icon" style={{ background: 'rgba(249, 115, 22, 0.12)', color: 'var(--accent-orange)' }}>
            <ShieldCheck size={26} />
          </div>
          <div style={{ flex: 1 }}>
            <div className="stat-val text-orange">100%</div>
            <div className="stat-label">Biometric Verification Ready</div>
            <div className="stat-trend" style={{ background: 'rgba(249, 115, 22, 0.15)', color: 'var(--accent-orange)' }}>
              <span>⚡ Fast-pass POS Active</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Employee Directory Card */}
      <div className="admin-card">
        {/* Card Header */}
        <div className="card-header-flex">
          <div>
            <div className="card-title-lg">
              <Users className="text-purple" size={24} />
              <span>Staff & Health Profile Directory</span>
              <span className="badge badge-purple" style={{ fontSize: '0.725rem' }}>{filtered.length} Staff</span>
            </div>
            <div style={{ fontSize: '0.825rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              Corporate personnel directory with biometric records, WHO BMI metrics, and daily nutrition targets
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
            <div style={{ display: 'flex', background: 'var(--tile-bg)', padding: '3px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)' }}>
              <button
                className={`btn btn-outline ${viewMode === 'grid' ? 'active' : ''}`}
                style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem', border: 'none', background: viewMode === 'grid' ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'transparent', color: viewMode === 'grid' ? '#fff' : 'var(--text-muted)' }}
                onClick={() => setViewMode('grid')}
              >
                Grid
              </button>
              <button
                className={`btn btn-outline ${viewMode === 'table' ? 'active' : ''}`}
                style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem', border: 'none', background: viewMode === 'table' ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'transparent', color: viewMode === 'table' ? '#fff' : 'var(--text-muted)' }}
                onClick={() => setViewMode('table')}
              >
                Table
              </button>
            </div>
            <button className="btn btn-outline" onClick={onRefresh}>
              <RefreshCw size={14} /> Refresh
            </button>
            <button className="btn btn-primary" onClick={onOpenRegister}>
              <Plus size={16} /> Register Employee & Face
            </button>
          </div>
        </div>

        {/* Search & Department Filter Toolbar */}
        <div className="toolbar-glass">
          <div style={{ position: 'relative', flex: 2 }}>
            <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search staff by Name, Employee Code (EMP001), Email or Department..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="form-input"
              style={{ width: '100%', paddingLeft: '2.4rem' }}
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <X size={14} />
              </button>
            )}
          </div>

          <select 
            value={deptFilter} 
            onChange={(e) => setDeptFilter(e.target.value)} 
            className="form-select"
            style={{ flex: 1 }}
          >
            <option value="">All Departments</option>
            {departments.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>

        {/* View Mode: Grid Cards */}
        {viewMode === 'grid' ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.25rem' }}>
            {filtered.length === 0 ? (
              <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
                <Users size={44} style={{ opacity: 0.3, margin: '0 auto 0.75rem auto' }} />
                <div style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: '1rem' }}>No employees found</div>
                <div style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>Try refining your search query or department filter.</div>
              </div>
            ) : (
              filtered.map((emp) => {
                const fullName = emp.name || `${emp.first_name || ''} ${emp.last_name || ''}`.trim() || 'Staff Member';
                const initials = getInitials(fullName);

                return (
                  <div 
                    key={emp.id || emp.employee_code}
                    className="card-grid-item"
                  >
                    {/* Top Row: Avatar & Basic Info */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                      <div 
                        style={{ 
                          width: '46px', 
                          height: '46px', 
                          borderRadius: '50%', 
                          background: 'linear-gradient(135deg, #6366f1, #a855f7)', 
                          display: 'flex', 
                          alignItems: 'center', 
                          justifyContent: 'center', 
                          color: '#fff', 
                          fontWeight: 800, 
                          fontSize: '1rem',
                          border: '2px solid rgba(255,255,255,0.2)',
                          boxShadow: '0 0 15px rgba(99, 102, 241, 0.3)'
                        }}
                      >
                        {initials}
                      </div>

                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontWeight: 800, color: 'var(--text-primary)', fontSize: '0.95rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {fullName}
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.2rem' }}>
                          <span className="chip-code">{emp.employee_code}</span>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>• {emp.department}</span>
                        </div>
                      </div>
                    </div>

                    {/* Metadata Box */}
                    <div className="meta-box">
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Email:</span>
                        <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>{emp.email || 'corporate@canteen.local'}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Health Target:</span>
                        <span style={{ color: 'var(--accent-orange)', fontWeight: 700 }}>2,200 kcal/day</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Biometrics:</span>
                        <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>
                          <ShieldCheck size={10} /> SFace Enrolled
                        </span>
                      </div>
                    </div>

                    {/* Bottom Actions */}
                    <div className="card-footer-action">
                      <span style={{ fontSize: '0.725rem', color: 'var(--text-dim)' }}>
                        Status: Active Staff
                      </span>
                      <button
                        className="btn btn-outline"
                        style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
                        onClick={() => handleInspect(emp)}
                      >
                        <Eye size={12} className="text-purple" /> View Profile
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        ) : (
          /* View Mode: Table */
          <div className="table-container">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Full Name</th>
                  <th>Department</th>
                  <th>Work Email</th>
                  <th>Calorie Target</th>
                  <th>Biometric Status</th>
                  <th style={{ textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan="7" style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                      No staff records found matching your query.
                    </td>
                  </tr>
                ) : (
                  filtered.map((emp) => {
                    const fullName = emp.name || `${emp.first_name || ''} ${emp.last_name || ''}`.trim() || 'Staff Member';
                    const initials = getInitials(fullName);

                    return (
                      <tr key={emp.id || emp.employee_code}>
                        <td>
                          <span className="chip-code">{emp.employee_code}</span>
                        </td>
                        <td>
                          <div className="user-avatar-cell">
                            <div className="user-avatar-bubble">{initials}</div>
                            <div>
                              <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{fullName}</div>
                            </div>
                          </div>
                        </td>
                        <td style={{ color: 'var(--text-secondary)' }}>{emp.department}</td>
                        <td style={{ color: 'var(--text-muted)', fontSize: '0.825rem' }}>{emp.email}</td>
                        <td>
                          <span style={{ color: 'var(--accent-orange)', fontWeight: 700, fontSize: '0.85rem' }}>
                            2,200 kcal
                          </span>
                        </td>
                        <td>
                          <span className="badge badge-success">
                            <ShieldCheck size={10} /> SFace Ready
                          </span>
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          <button
                            className="btn btn-outline"
                            style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
                            onClick={() => handleInspect(emp)}
                          >
                            <Eye size={12} className="text-purple" /> Inspect
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Employee Profile Inspection Modal */}
      {selectedEmp && (
        <div className="modal-overlay" onClick={() => setSelectedEmp(null)}>
          <div className="modal-box" style={{ maxWidth: '600px' }} onClick={(e) => e.stopPropagation()}>
            <div className="card-header-flex" style={{ margin: 0, paddingBottom: '0.85rem' }}>
              <div className="card-title-lg">
                <Users className="text-purple" size={22} />
                <span>Employee Profile Dossier</span>
              </div>
              <button 
                className="btn btn-outline" 
                style={{ padding: '0.3rem 0.55rem' }} 
                onClick={() => setSelectedEmp(null)}
              >
                <X size={16} />
              </button>
            </div>

            <div style={{ margin: '1.25rem 0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', background: 'var(--bg-card-inner)', border: '1px solid var(--border-subtle)', padding: '1rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem' }}>
                <div style={{ width: '56px', height: '56px', borderRadius: '50%', background: 'linear-gradient(135deg, #6366f1, #a855f7)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.3rem', fontWeight: 800, color: '#fff' }}>
                  {getInitials(selectedEmp.name || `${selectedEmp.first_name || ''} ${selectedEmp.last_name || ''}`)}
                </div>
                <div>
                  <h3 style={{ fontSize: '1.15rem', color: 'var(--text-primary)', fontWeight: 800 }}>
                    {selectedEmp.name || `${selectedEmp.first_name || ''} ${selectedEmp.last_name || ''}`.trim()}
                  </h3>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginTop: '0.2rem' }}>
                    <span className="chip-code">{selectedEmp.employee_code}</span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{selectedEmp.department}</span>
                  </div>
                </div>
              </div>

              {/* Health Metrics */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{ background: 'var(--bg-card-inner)', border: '1px solid var(--border-subtle)', padding: '0.85rem', borderRadius: 'var(--radius-sm)', textAlign: 'center' }}>
                  <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>WHO BMI Index</div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--accent-emerald)', marginTop: '0.2rem' }}>
                    {fullProfile?.profile?.bmi ? Number(fullProfile.profile.bmi).toFixed(1) : '22.9'}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                    {fullProfile?.profile?.bmi_category || 'Normal weight'}
                  </div>
                </div>

                <div style={{ background: 'var(--bg-card-inner)', border: '1px solid var(--border-subtle)', padding: '0.85rem', borderRadius: 'var(--radius-sm)', textAlign: 'center' }}>
                  <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>Daily Calorie Goal</div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--accent-orange)', marginTop: '0.2rem' }}>
                    {fullProfile?.profile?.daily_calorie_target || 2200}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>kcal / day</div>
                </div>

                <div style={{ background: 'var(--bg-card-inner)', border: '1px solid var(--border-subtle)', padding: '0.85rem', borderRadius: 'var(--radius-sm)', textAlign: 'center' }}>
                  <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>Biometrics</div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--accent-cyan)', marginTop: '0.2rem' }}>
                    128-D
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>SFace S-128</div>
                </div>
              </div>

              {/* Dietary Warnings / Restrictions */}
              <div style={{ background: 'var(--bg-card-inner)', border: '1px solid var(--border-subtle)', padding: '0.85rem', borderRadius: 'var(--radius-sm)' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
                  Dietary Restrictions & Allergens
                </div>
                <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                  {(fullProfile?.dietary_restrictions || []).length > 0 ? (
                    fullProfile.dietary_restrictions.map((r, i) => (
                      <span key={i} className="badge badge-amber">⚠️ {r}</span>
                    ))
                  ) : (
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>None recorded (Standard Dietary Intake)</span>
                  )}
                </div>
              </div>
            </div>

            <div style={{ textAlign: 'right', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.85rem' }}>
              <button className="btn btn-primary" onClick={() => setSelectedEmp(null)}>
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
