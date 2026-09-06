import React, { useState } from 'react';
import { 
  Utensils, Edit3, Check, DollarSign, RefreshCw, Flame, Search, 
  Sparkles, CheckCircle2, ShieldCheck, X, ArrowUpDown, Layers, Coffee
} from 'lucide-react';
import { foodsApi } from '../services/api';

export default function MenuPricingCatalog({ foods, onRefresh }) {
  const [editingId, setEditingId] = useState(null);
  const [editPrice, setEditPrice] = useState('');
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [viewMode, setViewMode] = useState('grid');

  const safeFoods = Array.isArray(foods) ? foods : [];

  const getDishCategory = (name = '') => {
    const n = name.toLowerCase();
    if (n.includes('rice') || n.includes('curry') || n.includes('dhal') || n.includes('mallum') || n.includes('sambol')) return 'Curries & Rice';
    if (n.includes('roll') || n.includes('samosa') || n.includes('vade') || n.includes('pan') || n.includes('pastry')) return 'Short Eats & Bakery';
    if (n.includes('hopper') || n.includes('roti') || n.includes('pittu') || n.includes('kiribath') || n.includes('noodle') || n.includes('kottu')) return 'Main Dishes';
    return 'Desserts & Extras';
  };

  const getDishEmoji = (name = '') => {
    const n = name.toLowerCase();
    if (n.includes('rice')) return '🍛';
    if (n.includes('chicken') || n.includes('meat')) return '🍗';
    if (n.includes('dhal') || n.includes('curry')) return '🥘';
    if (n.includes('noodle') || n.includes('kottu')) return '🍜';
    if (n.includes('hopper') || n.includes('roti') || n.includes('pittu')) return '🥞';
    if (n.includes('roll') || n.includes('samosa') || n.includes('vade') || n.includes('pan')) return '🥟';
    if (n.includes('watalappam') || n.includes('dessert')) return '🍮';
    return '🍽️';
  };

  const filtered = safeFoods.filter((food) => {
    const q = searchTerm.toLowerCase();
    const name = (food.name || food.display_name || '').toLowerCase();
    const cat = getDishCategory(food.name || food.display_name);

    const matchesSearch = name.includes(q);
    const matchesCat = categoryFilter === 'all' || cat === categoryFilter;
    return matchesSearch && matchesCat;
  });

  const avgPrice = safeFoods.length > 0 
    ? (safeFoods.reduce((acc, curr) => acc + (curr.price_lkr || curr.price || 0), 0) / safeFoods.length).toFixed(2)
    : '0.00';

  const startEdit = (food) => {
    setEditingId(food.id);
    setEditPrice(food.price_lkr || food.price || 0);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditPrice('');
  };

  const handleSavePrice = async (foodId) => {
    setSaving(true);
    try {
      await foodsApi.updatePrice(foodId, parseFloat(editPrice));
      setToast(`Updated price for food item #${foodId} to Rs. ${parseFloat(editPrice).toFixed(2)}`);
      setEditingId(null);
      onRefresh();
      setTimeout(() => setToast(null), 3500);
    } catch (err) {
      console.error(err);
      alert('Failed to update price: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      {/* Top Executive KPI Grid for Menu */}
      <div className="stats-grid">
        <div className="stat-box stat-orange">
          <div className="stat-icon" style={{ background: 'rgba(249, 115, 22, 0.12)', color: 'var(--accent-orange)' }}>
            <Utensils size={26} />
          </div>
          <div style={{ flex: 1 }}>
            <div className="stat-val text-orange">{safeFoods.length}</div>
            <div className="stat-label">Catalog Menu Items</div>
            <div className="stat-trend" style={{ background: 'rgba(249, 115, 22, 0.15)', color: 'var(--accent-orange)' }}>
              <CheckCircle2 size={10} /> YOLO11n Multi-Class Ready
            </div>
          </div>
        </div>

        <div className="stat-box stat-emerald">
          <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.12)', color: 'var(--accent-emerald)' }}>
            <DollarSign size={26} />
          </div>
          <div style={{ flex: 1 }}>
            <div className="stat-val text-emerald">Rs. {avgPrice}</div>
            <div className="stat-label">Average Item Price</div>
            <div className="stat-trend" style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-emerald)' }}>
              <span>⚡ Live Dynamic Pricing</span>
            </div>
          </div>
        </div>

        <div className="stat-box stat-cyan">
          <div className="stat-icon" style={{ background: 'rgba(6, 182, 212, 0.12)', color: 'var(--accent-cyan)' }}>
            <ShieldCheck size={26} />
          </div>
          <div style={{ flex: 1 }}>
            <div className="stat-val text-cyan">MRI & USDA</div>
            <div className="stat-label">Nutritional Provenance</div>
            <div className="stat-trend" style={{ background: 'rgba(6, 182, 212, 0.15)', color: 'var(--accent-cyan)' }}>
              <span>🇱🇰 Sri Lanka Standard 2022</span>
            </div>
          </div>
        </div>

        <div className="stat-box stat-purple">
          <div className="stat-icon" style={{ background: 'rgba(168, 85, 247, 0.12)', color: 'var(--accent-purple)' }}>
            <Layers size={26} />
          </div>
          <div style={{ flex: 1 }}>
            <div className="stat-val text-purple">4 Categories</div>
            <div className="stat-label">Canteen Food Segments</div>
            <div className="stat-trend" style={{ background: 'rgba(168, 85, 247, 0.15)', color: 'var(--accent-purple)' }}>
              <span>🍛 Rice, Snacks & Short Eats</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Menu Catalog Card */}
      <div className="admin-card">
        {/* Card Header */}
        <div className="card-header-flex">
          <div>
            <div className="card-title-lg">
              <Utensils className="text-orange" size={24} />
              <span>Food Catalog & Dynamic Menu Pricing</span>
              <span className="badge badge-amber" style={{ fontSize: '0.725rem' }}>{filtered.length} Dishes</span>
            </div>
            <div style={{ fontSize: '0.825rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              Manage item pricing, portion sizes, and verified nutritional benchmarks for AI plate billing
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
          </div>
        </div>

        {/* Toast Notification */}
        {toast && (
          <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', color: 'var(--accent-emerald)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', marginBottom: '1.25rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <CheckCircle2 size={16} />
            <span>{toast}</span>
          </div>
        )}

        {/* Search & Category Filter Toolbar */}
        <div className="toolbar-glass">
          <div style={{ position: 'relative', flex: 2 }}>
            <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search dishes by name (e.g. Rice & Curry, Hoppers, Roll)..."
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

          <div style={{ display: 'flex', gap: '0.35rem', overflowX: 'auto' }}>
            {['all', 'Curries & Rice', 'Short Eats & Bakery', 'Main Dishes', 'Desserts & Extras'].map((cat) => (
              <button
                key={cat}
                className={`btn btn-outline ${categoryFilter === cat ? 'active' : ''}`}
                style={{
                  padding: '0.4rem 0.8rem',
                  fontSize: '0.75rem',
                  border: '1px solid var(--border-glass)',
                  background: categoryFilter === cat ? 'linear-gradient(135deg, #f97316, #ea580c)' : 'transparent',
                  color: categoryFilter === cat ? '#fff' : 'var(--text-muted)',
                  fontWeight: categoryFilter === cat ? 700 : 500,
                }}
                onClick={() => setCategoryFilter(cat)}
              >
                {cat === 'all' ? 'All Dishes' : cat}
              </button>
            ))}
          </div>
        </div>

        {/* View Mode: Grid Cards */}
        {viewMode === 'grid' ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.25rem' }}>
            {filtered.length === 0 ? (
              <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
                <Utensils size={44} style={{ opacity: 0.3, margin: '0 auto 0.75rem auto' }} />
                <div style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: '1rem' }}>No dishes found</div>
                <div style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>Try clearing your search query.</div>
              </div>
            ) : (
              filtered.map((food) => {
                const isEditing = editingId === food.id;
                const cals = food.nutrition?.energy_kcal || food.calories_kcal || 0;
                const protein = food.nutrition?.protein_g || food.protein_g || 0;
                const carbs = food.nutrition?.carbs_g || food.carbs_g || 0;
                const fat = food.nutrition?.fat_g || food.fat_g || 0;
                const price = food.price_lkr || food.price || 0;
                const category = getDishCategory(food.name || food.display_name);
                const emoji = getDishEmoji(food.name || food.display_name);

                return (
                  <div
                    key={food.id}
                    className="card-grid-item"
                  >
                    {/* Top Row: Emoji & Name */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                      <div 
                        style={{ 
                          width: '48px', 
                          height: '48px', 
                          borderRadius: 'var(--radius-sm)', 
                          background: 'linear-gradient(135deg, #f97316, #fbbf24)', 
                          display: 'flex', 
                          alignItems: 'center', 
                          justifyContent: 'center', 
                          fontSize: '1.4rem',
                          flexShrink: 0,
                          boxShadow: '0 0 15px rgba(249, 115, 22, 0.25)'
                        }}
                      >
                        {emoji}
                      </div>

                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontWeight: 800, color: 'var(--text-primary)', fontSize: '0.95rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {food.display_name || food.name}
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.2rem' }}>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{category}</span>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>• #{food.id}</span>
                        </div>
                      </div>
                    </div>

                    {/* Nutrition Macros Box */}
                    <div className="meta-box">
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.4rem', textAlign: 'center', fontSize: '0.725rem' }}>
                        <div>
                          <div style={{ color: 'var(--text-muted)', fontSize: '0.65rem' }}>CALORIES</div>
                          <div style={{ fontWeight: 800, color: 'var(--accent-orange)', marginTop: '2px' }}>{cals.toFixed(0)}</div>
                        </div>
                        <div>
                          <div style={{ color: 'var(--text-muted)', fontSize: '0.65rem' }}>PROTEIN</div>
                          <div style={{ fontWeight: 800, color: 'var(--accent-cyan)', marginTop: '2px' }}>{protein.toFixed(1)}g</div>
                        </div>
                        <div>
                          <div style={{ color: 'var(--text-muted)', fontSize: '0.65rem' }}>CARBS</div>
                          <div style={{ fontWeight: 800, color: 'var(--accent-amber)', marginTop: '2px' }}>{carbs.toFixed(1)}g</div>
                        </div>
                        <div>
                          <div style={{ color: 'var(--text-muted)', fontSize: '0.65rem' }}>FAT</div>
                          <div style={{ fontWeight: 800, color: 'var(--accent-rose)', marginTop: '2px' }}>{fat.toFixed(1)}g</div>
                        </div>
                      </div>
                    </div>

                    {/* Bottom Row: Price & Inline Edit */}
                    <div className="card-footer-action">
                      <div>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Standard Price</span>
                        {isEditing ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.2rem' }}>
                            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent-emerald)' }}>Rs.</span>
                            <input
                              type="number"
                              step="5"
                              value={editPrice}
                              onChange={(e) => setEditPrice(e.target.value)}
                              className="form-input"
                              style={{ width: '85px', padding: '0.25rem 0.5rem', fontSize: '0.85rem', fontWeight: 700 }}
                              autoFocus
                            />
                          </div>
                        ) : (
                          <div style={{ fontFamily: 'var(--font-heading)', fontSize: '1.25rem', fontWeight: 900, color: 'var(--accent-emerald)' }}>
                            Rs. {parseFloat(price).toFixed(2)}
                          </div>
                        )}
                      </div>

                      <div>
                        {isEditing ? (
                          <div style={{ display: 'flex', gap: '0.4rem' }}>
                            <button
                              className="btn btn-success"
                              style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}
                              onClick={() => handleSavePrice(food.id)}
                              disabled={saving}
                            >
                              <Check size={12} /> {saving ? 'Saving...' : 'Save'}
                            </button>
                            <button
                              className="btn btn-outline"
                              style={{ padding: '0.35rem 0.55rem', fontSize: '0.75rem' }}
                              onClick={cancelEdit}
                              disabled={saving}
                            >
                              <X size={12} />
                            </button>
                          </div>
                        ) : (
                          <button
                            className="btn btn-outline"
                            style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
                            onClick={() => startEdit(food)}
                          >
                            <Edit3 size={12} className="text-orange" /> Edit Price
                          </button>
                        )}
                      </div>
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
                  <th>ID</th>
                  <th>Dish Name</th>
                  <th>Category</th>
                  <th>Portion</th>
                  <th>Energy (kcal)</th>
                  <th>Protein</th>
                  <th>Price (LKR)</th>
                  <th style={{ textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan="8" style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                      No dishes found in menu catalog.
                    </td>
                  </tr>
                ) : (
                  filtered.map((food) => {
                    const isEditing = editingId === food.id;
                    const cals = food.nutrition?.energy_kcal || food.calories_kcal || 0;
                    const protein = food.nutrition?.protein_g || food.protein_g || 0;
                    const price = food.price_lkr || food.price || 0;
                    const category = getDishCategory(food.name || food.display_name);
                    const emoji = getDishEmoji(food.name || food.display_name);

                    return (
                      <tr key={food.id}>
                        <td>
                          <span className="chip-code">#{food.id}</span>
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                            <span style={{ fontSize: '1.2rem' }}>{emoji}</span>
                            <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                              {food.display_name || food.name}
                            </span>
                          </div>
                        </td>
                        <td style={{ color: 'var(--text-secondary)' }}>{category}</td>
                        <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{food.portion_size || '1 portion (150g)'}</td>
                        <td style={{ color: 'var(--accent-orange)', fontWeight: 700 }}>
                          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
                            <Flame size={12} /> {cals.toFixed(0)} kcal
                          </span>
                        </td>
                        <td style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>{protein.toFixed(1)}g</td>
                        <td>
                          {isEditing ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                              <span style={{ fontSize: '0.8rem', color: 'var(--accent-emerald)', fontWeight: 700 }}>Rs.</span>
                              <input
                                type="number"
                                step="5"
                                value={editPrice}
                                onChange={(e) => setEditPrice(e.target.value)}
                                className="form-input"
                                style={{ width: '80px', padding: '0.25rem 0.5rem', fontSize: '0.8rem', fontWeight: 700 }}
                                autoFocus
                              />
                            </div>
                          ) : (
                            <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 800, color: 'var(--accent-emerald)', fontSize: '0.95rem' }}>
                              Rs. {parseFloat(price).toFixed(2)}
                            </span>
                          )}
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          {isEditing ? (
                            <div style={{ display: 'inline-flex', gap: '0.35rem' }}>
                              <button
                                className="btn btn-success"
                                style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                                onClick={() => handleSavePrice(food.id)}
                                disabled={saving}
                              >
                                <Check size={12} /> Save
                              </button>
                              <button
                                className="btn btn-outline"
                                style={{ padding: '0.3rem 0.5rem', fontSize: '0.75rem' }}
                                onClick={cancelEdit}
                                disabled={saving}
                              >
                                <X size={12} />
                              </button>
                            </div>
                          ) : (
                            <button
                              className="btn btn-outline"
                              style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
                              onClick={() => startEdit(food)}
                            >
                              <Edit3 size={12} className="text-orange" /> Edit Price
                            </button>
                          )}
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
    </div>
  );
}
