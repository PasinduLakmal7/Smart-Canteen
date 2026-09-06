import React, { useState } from 'react';
import { 
  Receipt, Search, Filter, RefreshCw, DollarSign, Utensils, Eye, X, 
  CheckCircle, Flame, Calendar, TrendingUp, Copy, Check, Download, 
  Printer, ArrowUpRight, ShieldCheck, Sparkles, Clock, PieChart, Layers
} from 'lucide-react';

export default function TransactionLedger({ transactions, analytics, onRefresh }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedTx, setSelectedTx] = useState(null);
  const [copiedCode, setCopiedCode] = useState(null);
  const [timeFilter, setTimeFilter] = useState('all');

  const handleCopy = (code) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const filtered = transactions.filter((tx) => {
    const q = searchTerm.toLowerCase();
    const matchesSearch = (
      tx.transaction_code?.toLowerCase().includes(q) ||
      tx.employee_code?.toLowerCase().includes(q) ||
      tx.employee_name?.toLowerCase().includes(q) ||
      tx.department?.toLowerCase().includes(q)
    );
    const matchesDept = !departmentFilter || tx.department === departmentFilter;
    const matchesStatus = !statusFilter || tx.payment_status === statusFilter;
    
    let matchesTime = true;
    if (timeFilter === 'today') {
      const todayStr = new Date().toISOString().split('T')[0];
      matchesTime = tx.transaction_date?.startsWith(todayStr);
    }

    return matchesSearch && matchesDept && matchesStatus && matchesTime;
  });

  const topDishes = analytics?.top_dishes || [];
  const maxOrders = Math.max(...topDishes.map((d) => d.total_ordered || 1), 1);

  // Export filtered transactions to CSV
  const handleExportCSV = () => {
    if (filtered.length === 0) return;
    const headers = ['TX Reference', 'Date & Time', 'Employee Code', 'Employee Name', 'Department', 'Dishes', 'Calories (kcal)', 'Total (LKR)', 'Status'];
    const rows = filtered.map((tx) => [
      tx.transaction_code,
      `"${tx.transaction_date}"`,
      tx.employee_code,
      `"${tx.employee_name}"`,
      `"${tx.department}"`,
      `"${tx.items?.map((it) => `${it.display_name || it.food_name} (x${it.quantity})`).join('; ')}"`,
      tx.total_calories || 0,
      tx.total_amount || 0,
      tx.payment_status,
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `smart_canteen_ledger_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getDishEmoji = (name = '') => {
    const n = name.toLowerCase();
    if (n.includes('rice')) return '🍛';
    if (n.includes('chicken') || n.includes('meat')) return '🍗';
    if (n.includes('dhal') || n.includes('curry')) return '🥘';
    if (n.includes('noodle') || n.includes('kottu')) return '🍜';
    if (n.includes('hopper') || n.includes('roti') || n.includes('pittu')) return '🥞';
    if (n.includes('roll') || n.includes('samosa') || n.includes('vade')) return '🥟';
    return '🍽️';
  };

  const formatFriendlyTime = (dateStr) => {
    if (!dateStr) return '—';
    try {
      const d = new Date(dateStr.replace(' ', 'T'));
      if (isNaN(d.getTime())) return dateStr;
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return dateStr;
    }
  };

  return (
    <div>
      {/* Top Executive KPI Grid */}
      <div className="stats-grid">
        {/* Stat 1: Total Revenue */}
        <div className="stat-box stat-emerald">
          <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.12)', color: 'var(--accent-emerald)' }}>
            <DollarSign size={26} />
          </div>
          <div style={{ flex: 1 }}>
            <div className="stat-val text-emerald">
              {analytics?.formatted_total_revenue || `Rs. ${(analytics?.total_revenue_lkr || 0).toFixed(2)}`}
            </div>
            <div className="stat-label">Total Canteen Revenue</div>
            <div className="stat-trend" style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-emerald)' }}>
              <CheckCircle size={10} /> 100% Payroll Reconciled
            </div>
          </div>
        </div>

        {/* Stat 2: Total Meals */}
        <div className="stat-box stat-cyan">
          <div className="stat-icon" style={{ background: 'rgba(6, 182, 212, 0.12)', color: 'var(--accent-cyan)' }}>
            <Receipt size={26} />
          </div>
          <div style={{ flex: 1 }}>
            <div className="stat-val text-cyan">
              {analytics?.total_transactions || transactions.length}
            </div>
            <div className="stat-label">Total Meals Recorded</div>
            <div className="stat-trend" style={{ background: 'rgba(6, 182, 212, 0.15)', color: 'var(--accent-cyan)' }}>
              <Layers size={10} /> AI Counter Dispatches
            </div>
          </div>
        </div>

        {/* Stat 3: Today's Revenue */}
        <div className="stat-box stat-orange">
          <div className="stat-icon" style={{ background: 'rgba(249, 115, 22, 0.12)', color: 'var(--accent-orange)' }}>
            <TrendingUp size={26} />
          </div>
          <div style={{ flex: 1 }}>
            <div className="stat-val text-orange">
              {analytics?.formatted_today_revenue || `Rs. ${(analytics?.today_revenue_lkr || 0).toFixed(2)}`}
            </div>
            <div className="stat-label">Today's Sales Revenue</div>
            <div className="stat-trend" style={{ background: 'rgba(249, 115, 22, 0.15)', color: 'var(--accent-orange)' }}>
              <Clock size={10} /> Live Counter Volume
            </div>
          </div>
        </div>

        {/* Stat 4: Total Calories */}
        <div className="stat-box stat-purple">
          <div className="stat-icon" style={{ background: 'rgba(168, 85, 247, 0.12)', color: 'var(--accent-purple)' }}>
            <Flame size={26} />
          </div>
          <div style={{ flex: 1 }}>
            <div className="stat-val text-purple">
              {(analytics?.total_calories_served || 0).toLocaleString()} kcal
            </div>
            <div className="stat-label">Total Calories Dispensed</div>
            <div className="stat-trend" style={{ background: 'rgba(168, 85, 247, 0.15)', color: 'var(--accent-purple)' }}>
              <PieChart size={10} /> Nutrition Engine Synced
            </div>
          </div>
        </div>
      </div>

      {/* Top 5 Most Popular Sri Lankan Dishes Showcase */}
      {topDishes.length > 0 && (
        <div className="admin-card" style={{ padding: '1.35rem 1.6rem', marginBottom: '1.75rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem', fontFamily: 'var(--font-heading)' }}>
              <Utensils size={18} className="text-orange" />
              <span>Trending Sri Lankan Canteen Specialties</span>
              <span className="badge badge-amber" style={{ fontSize: '0.7rem' }}>Top Popular</span>
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Ranked by consumption volume</span>
          </div>

          <div className="ranking-grid">
            {topDishes.slice(0, 5).map((dish, i) => {
              const medalColors = [
                { bg: 'linear-gradient(135deg, #fbbf24, #d97706)', text: '#000', label: '1st' },
                { bg: 'linear-gradient(135deg, #cbd5e1, #94a3b8)', text: '#000', label: '2nd' },
                { bg: 'linear-gradient(135deg, #d97706, #92400e)', text: '#fff', label: '3rd' },
                { bg: 'var(--border-subtle)', text: 'var(--text-secondary)', label: `#${i + 1}` },
                { bg: 'var(--border-subtle)', text: 'var(--text-secondary)', label: `#${i + 1}` },
              ];
              const medal = medalColors[i] || medalColors[3];
              const pct = Math.round((dish.total_ordered / maxOrders) * 100);

              return (
                <div key={i} className="ranking-tile">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flex: 1, minWidth: 0 }}>
                    <div 
                      className="ranking-badge" 
                      style={{ background: medal.bg, color: medal.text, boxShadow: i < 3 ? '0 0 10px rgba(245, 158, 11, 0.3)' : 'none' }}
                    >
                      {medal.label}
                    </div>
                    <div style={{ fontSize: '1.2rem' }}>{getDishEmoji(dish.food_name || dish.display_name)}</div>
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.85rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={dish.display_name}>
                        {dish.display_name || dish.food_name}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.2rem' }}>
                        <div style={{ height: '4px', background: 'var(--border-glass)', borderRadius: '2px', flex: 1, overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: `${pct}%`, background: 'linear-gradient(90deg, #f97316, #fbbf24)', borderRadius: '2px' }} />
                        </div>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600 }}>{dish.total_ordered} orders</span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Main Transactions Audit Card */}
      <div className="admin-card">
        {/* Card Header */}
        <div className="card-header-flex">
          <div>
            <div className="card-title-lg">
              <Receipt className="text-cyan" size={24} />
              <span>Executive Meal Ledger & Payroll Audit</span>
              <span className="badge badge-purple" style={{ fontSize: '0.725rem' }}>Phase 5 Active</span>
            </div>
            <div style={{ fontSize: '0.825rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              Immutable financial transaction ledger with permanent price and macronutrient snapshots
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
            <button className="btn btn-outline" onClick={handleExportCSV} title="Export current view as CSV">
              <Download size={14} /> Export CSV
            </button>
            <button className="btn btn-outline" onClick={onRefresh} title="Reload live database records">
              <RefreshCw size={14} /> Refresh
            </button>
          </div>
        </div>

        {/* Toolbar: Search, Filters & Time Range */}
        <div className="toolbar-glass">
          {/* Search Box */}
          <div style={{ position: 'relative', flex: 2 }}>
            <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search by TX code (TX-...), Employee ID, Name or Department..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="form-input"
              style={{ width: '100%', paddingLeft: '2.4rem', paddingRight: searchTerm ? '2rem' : '0.95rem' }}
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

          {/* Department Filter */}
          <select 
            value={departmentFilter} 
            onChange={(e) => setDepartmentFilter(e.target.value)} 
            className="form-select"
            style={{ flex: 1 }}
          >
            <option value="">All Departments</option>
            <option value="IT / Engineering">IT / Engineering</option>
            <option value="Engineering">Engineering</option>
            <option value="Human Resources">Human Resources</option>
            <option value="Finance & Accounting">Finance & Accounting</option>
            <option value="Operations">Operations</option>
            <option value="Marketing">Marketing</option>
            <option value="Executive">Executive</option>
          </select>

          {/* Status Filter */}
          <select 
            value={statusFilter} 
            onChange={(e) => setStatusFilter(e.target.value)} 
            className="form-select"
            style={{ flex: 1 }}
          >
            <option value="">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="payroll_deducted">Payroll Deducted</option>
            <option value="pending">Pending</option>
          </select>

          {/* Quick Time Filter */}
          <div style={{ display: 'flex', background: 'var(--tile-bg)', padding: '3px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)' }}>
            <button
              className={`btn btn-outline ${timeFilter === 'all' ? 'active' : ''}`}
              style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem', border: 'none', background: timeFilter === 'all' ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'transparent', color: timeFilter === 'all' ? '#fff' : 'var(--text-muted)' }}
              onClick={() => setTimeFilter('all')}
            >
              All
            </button>
            <button
              className={`btn btn-outline ${timeFilter === 'today' ? 'active' : ''}`}
              style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem', border: 'none', background: timeFilter === 'today' ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'transparent', color: timeFilter === 'today' ? '#fff' : 'var(--text-muted)' }}
              onClick={() => setTimeFilter('today')}
            >
              Today
            </button>
          </div>
        </div>

        {/* High-Precision Transaction Ledger Table */}
        <div className="table-container">
          <table className="admin-table">
            <thead>
              <tr>
                <th>TX Reference</th>
                <th>Date & Time</th>
                <th>Employee</th>
                <th>Department</th>
                <th>Dishes & Portions</th>
                <th>Energy</th>
                <th>Amount (LKR)</th>
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Audit</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan="9" style={{ textAlign: 'center', padding: '3.5rem 1rem', color: 'var(--text-muted)' }}>
                    <Receipt size={40} style={{ opacity: 0.3, margin: '0 auto 0.75rem auto' }} />
                    <div style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: '1rem' }}>No transaction records found</div>
                    <div style={{ fontSize: '0.8rem', marginTop: '0.3rem' }}>Try clearing filters or search query above.</div>
                  </td>
                </tr>
              ) : (
                filtered.map((tx) => {
                  const itemsList = tx.items || [];
                  const initials = (tx.employee_name || 'Staff')
                    .split(' ')
                    .map((n) => n[0])
                    .slice(0, 2)
                    .join('')
                    .toUpperCase();

                  return (
                    <tr key={tx.id || tx.transaction_code}>
                      {/* TX Reference Chip with Copy */}
                      <td>
                        <button
                          onClick={() => handleCopy(tx.transaction_code)}
                          className="chip-code"
                          title="Click to copy Transaction ID"
                          style={{ cursor: 'pointer', border: 'none', textAlign: 'left' }}
                        >
                          <span>{tx.transaction_code}</span>
                          {copiedCode === tx.transaction_code ? (
                            <Check size={12} className="text-emerald" />
                          ) : (
                            <Copy size={12} style={{ opacity: 0.5 }} />
                          )}
                        </button>
                      </td>

                      {/* Date & Time */}
                      <td>
                        <div style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: '0.825rem' }}>
                          {formatFriendlyTime(tx.transaction_date)}
                        </div>
                        <div style={{ color: 'var(--text-muted)', fontSize: '0.725rem' }}>
                          {tx.transaction_date?.split(' ')[0] || tx.transaction_date}
                        </div>
                      </td>

                      {/* Employee Cell with Avatar */}
                      <td>
                        <div className="user-avatar-cell">
                          <div className="user-avatar-bubble">
                            {initials}
                          </div>
                          <div>
                            <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.875rem' }}>
                              {tx.employee_name}
                            </div>
                            <div style={{ fontSize: '0.725rem', color: 'var(--accent-cyan)', fontWeight: 600 }}>
                              {tx.employee_code}
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Department */}
                      <td>
                        <span style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                          {tx.department}
                        </span>
                      </td>

                      {/* Dishes List */}
                      <td style={{ maxWidth: '280px' }}>
                        <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                          {itemsList.slice(0, 2).map((it, idx) => (
                            <span 
                              key={idx}
                              style={{ 
                                background: 'var(--tile-bg)', 
                                border: '1px solid var(--border-subtle)',
                                padding: '0.15rem 0.5rem', 
                                borderRadius: 'var(--radius-xs)', 
                                fontSize: '0.75rem',
                                color: 'var(--text-primary)',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '0.25rem'
                              }}
                            >
                              <span>{getDishEmoji(it.food_name)}</span>
                              <span>{it.display_name || it.food_name}</span>
                              {it.quantity > 1 && <strong style={{ color: 'var(--accent-cyan)' }}>x{it.quantity}</strong>}
                            </span>
                          ))}
                          {itemsList.length > 2 && (
                            <span style={{ fontSize: '0.725rem', color: 'var(--text-muted)', padding: '0.15rem 0.35rem' }}>
                              +{itemsList.length - 2} more
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Energy */}
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', color: 'var(--accent-orange)', fontWeight: 700, fontSize: '0.85rem' }}>
                          <Flame size={14} />
                          <span>{tx.total_calories?.toFixed(0)} kcal</span>
                        </div>
                      </td>

                      {/* Total Amount */}
                      <td>
                        <div style={{ fontFamily: 'var(--font-heading)', fontWeight: 800, color: 'var(--text-primary)', fontSize: '0.95rem', fontVariantNumeric: 'tabular-nums' }}>
                          {tx.formatted_total_amount || `Rs. ${tx.total_amount?.toFixed(2)}`}
                        </div>
                      </td>

                      {/* Payment Status */}
                      <td>
                        <span className="badge badge-success">
                          <span className="live-beacon" style={{ width: '5px', height: '5px' }}></span>
                          {tx.payment_status}
                        </span>
                      </td>

                      {/* Actions */}
                      <td style={{ textAlign: 'right' }}>
                        <button
                          className="btn btn-outline"
                          style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
                          onClick={() => setSelectedTx(tx)}
                        >
                          <Eye size={12} className="text-cyan" /> Inspect
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* POS Receipt & Nutrition Snapshot Inspector Modal */}
      {selectedTx && (
        <div className="modal-overlay" onClick={() => setSelectedTx(null)}>
          <div className="modal-box" style={{ maxWidth: '620px' }} onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="card-header-flex" style={{ margin: 0, paddingBottom: '0.85rem' }}>
              <div className="card-title-lg">
                <Receipt className="text-cyan" size={22} />
                <span>POS Receipt Inspector</span>
              </div>
              <button 
                className="btn btn-outline" 
                style={{ padding: '0.3rem 0.55rem' }} 
                onClick={() => setSelectedTx(null)}
              >
                <X size={16} />
              </button>
            </div>

            {/* Simulated Printed POS Receipt Body */}
            <div style={{ margin: '1.25rem 0', background: 'var(--bg-card-inner)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '1.5rem', position: 'relative' }}>
              {/* Receipt Header */}
              <div style={{ textAlign: 'center', borderBottom: '1px dashed var(--border-glass)', paddingBottom: '1rem', marginBottom: '1rem' }}>
                <div style={{ fontSize: '1.1rem', fontWeight: 900, letterSpacing: '0.05em', color: 'var(--text-primary)', fontFamily: 'var(--font-heading)' }}>
                  SMART CANTEEN ENTERPRISE POS
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                  Live Multi-Modal AI Billing & Nutrition Subsystem
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)', fontWeight: 700, marginTop: '0.35rem', fontFamily: 'var(--font-mono)' }}>
                  {selectedTx.transaction_code}
                </div>
              </div>

              {/* Employee & Time Metadata */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.825rem', marginBottom: '1.25rem', background: 'var(--tile-bg)', border: '1px solid var(--border-subtle)', padding: '0.85rem', borderRadius: 'var(--radius-sm)' }}>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Staff Member:</span>{' '}
                  <strong style={{ color: 'var(--text-primary)' }}>{selectedTx.employee_name}</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Staff Code:</span>{' '}
                  <span className="chip-code" style={{ padding: '0.1rem 0.4rem' }}>{selectedTx.employee_code}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Department:</span>{' '}
                  <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>{selectedTx.department}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Timestamp:</span>{' '}
                  <span style={{ color: 'var(--text-secondary)' }}>{selectedTx.transaction_date}</span>
                </div>
              </div>

              {/* Itemized Foods Table */}
              <div style={{ marginBottom: '1.25rem' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.5rem', letterSpacing: '0.05em' }}>
                  Itemized Plate Detection
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  {(selectedTx.items || []).map((item, idx) => (
                    <div 
                      key={idx}
                      style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center', 
                        padding: '0.45rem 0.65rem', 
                        background: 'var(--tile-bg)', 
                        borderRadius: 'var(--radius-xs)',
                        fontSize: '0.825rem',
                        border: '1px solid var(--border-subtle)'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span>{getDishEmoji(item.food_name)}</span>
                        <strong style={{ color: 'var(--text-primary)' }}>{item.display_name || item.food_name}</strong>
                        {item.quantity > 1 && <span className="chip-code" style={{ padding: '0 0.3rem' }}>x{item.quantity}</span>}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{item.calories_kcal?.toFixed(0)} kcal</span>
                        <span style={{ fontWeight: 800, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>
                          {item.formatted_total_price || `Rs. ${item.total_price?.toFixed(2)}`}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Nutrition Snapshot Breakdown */}
              <div style={{ background: 'var(--tile-bg)', border: '1px solid var(--border-subtle)', padding: '0.85rem', borderRadius: 'var(--radius-sm)', marginBottom: '1.25rem' }}>
                <div style={{ fontSize: '0.725rem', fontWeight: 800, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                  Nutritional Intake Snapshot
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.4rem', textAlign: 'center', fontSize: '0.75rem' }}>
                  <div style={{ background: 'rgba(6, 182, 212, 0.1)', padding: '0.4rem', borderRadius: 'var(--radius-xs)', border: '1px solid rgba(6, 182, 212, 0.2)' }}>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.675rem' }}>PROTEIN</div>
                    <div style={{ fontWeight: 800, color: 'var(--accent-cyan)', marginTop: '2px' }}>{selectedTx.total_protein_g?.toFixed(1) || '—'}g</div>
                  </div>
                  <div style={{ background: 'rgba(245, 158, 11, 0.1)', padding: '0.4rem', borderRadius: 'var(--radius-xs)', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.675rem' }}>CARBS</div>
                    <div style={{ fontWeight: 800, color: 'var(--accent-amber)', marginTop: '2px' }}>{selectedTx.total_carbs_g?.toFixed(1) || '—'}g</div>
                  </div>
                  <div style={{ background: 'rgba(244, 63, 94, 0.1)', padding: '0.4rem', borderRadius: 'var(--radius-xs)', border: '1px solid rgba(244, 63, 94, 0.2)' }}>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.675rem' }}>FAT</div>
                    <div style={{ fontWeight: 800, color: 'var(--accent-rose)', marginTop: '2px' }}>{selectedTx.total_fat_g?.toFixed(1) || '—'}g</div>
                  </div>
                  <div style={{ background: 'rgba(16, 185, 129, 0.1)', padding: '0.4rem', borderRadius: 'var(--radius-xs)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.675rem' }}>CALORIES</div>
                    <div style={{ fontWeight: 800, color: 'var(--accent-emerald)', marginTop: '2px' }}>{selectedTx.total_calories?.toFixed(0)} kcal</div>
                  </div>
                </div>
              </div>

              {/* Total Financial Summary */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '2px solid var(--border-glass)', paddingTop: '0.85rem' }}>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Settlement Status</div>
                  <div className="badge badge-success" style={{ marginTop: '0.2rem' }}>
                    <CheckCircle size={12} /> {selectedTx.payment_status}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Total Payroll Billed</div>
                  <div style={{ fontFamily: 'var(--font-heading)', fontSize: '1.4rem', fontWeight: 900, color: 'var(--accent-emerald)' }}>
                    {selectedTx.formatted_total_amount || `Rs. ${selectedTx.total_amount?.toFixed(2)}`}
                  </div>
                </div>
              </div>
            </div>

            {/* Modal Actions */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.6rem' }}>
              <button className="btn btn-outline" onClick={() => window.print()}>
                <Printer size={14} /> Print Slip
              </button>
              <button className="btn btn-primary" onClick={() => setSelectedTx(null)}>
                Close Audit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
