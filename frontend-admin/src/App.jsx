import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { employeeApi, faceApi, foodsApi, transactionApi } from './services/api';
import EmployeeDirectory from './components/EmployeeDirectory';
import FaceGallery from './components/FaceGallery';
import MenuPricingCatalog from './components/MenuPricingCatalog';
import BenchmarkEvaluator from './components/BenchmarkEvaluator';
import TransactionLedger from './components/TransactionLedger';
import RecommendationInsights from './components/RecommendationInsights';
import UnifiedRegisterModal from './components/UnifiedRegisterModal';
import { Users, Camera, Utensils, Gauge, Plus, ExternalLink, ShieldCheck, Zap, AlertCircle, Receipt, Sparkles } from 'lucide-react';

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();

  const [employees, setEmployees] = useState([]);
  const [enrolledFaces, setEnrolledFaces] = useState([]);
  const [foods, setFoods] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    setFetchError(null);
    try {
      const [empList, faceList, foodList, txList, analyticsData] = await Promise.all([
        employeeApi.list().catch((err) => {
          console.error('Error fetching employees:', err);
          return [];
        }),
        faceApi.listEnrolled().catch((err) => {
          console.error('Error fetching enrolled faces:', err);
          return [];
        }),
        foodsApi.list().catch((err) => {
          console.error('Error fetching foods:', err);
          return [];
        }),
        transactionApi.list().catch((err) => {
          console.error('Error fetching transactions:', err);
          return [];
        }),
        transactionApi.getAnalytics().catch((err) => {
          console.error('Error fetching analytics:', err);
          return null;
        }),
      ]);
      setEmployees(Array.isArray(empList) ? empList : []);
      setEnrolledFaces(Array.isArray(faceList) ? faceList : []);
      setFoods(Array.isArray(foodList) ? foodList : []);
      setTransactions(Array.isArray(txList) ? txList : []);
      setAnalytics(analyticsData);
    } catch (err) {
      console.error('Error fetching admin data:', err);
      setFetchError(err.message || 'Failed to connect to backend server');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleDeactivateFace = async (empCode) => {
    if (!window.confirm(`Are you sure you want to deactivate face biometrics for ${empCode}?`)) return;
    try {
      await faceApi.deactivate(empCode);
      fetchData();
    } catch (err) {
      alert(err.message || 'Deactivation failed');
    }
  };

  const [theme, setTheme] = useState(() => localStorage.getItem('canteen_theme') || 'dark');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('canteen_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const safeEmployees = Array.isArray(employees) ? employees : [];
  const safeFaces = Array.isArray(enrolledFaces) ? enrolledFaces : [];
  const safeFoods = Array.isArray(foods) ? foods : [];
  const safeTxs = Array.isArray(transactions) ? transactions : [];

  const currentPath = location.pathname;

  return (
    <div className="admin-app">
      {/* Top Header */}
      <header className="admin-header">
        <div className="admin-brand">
          <div className="admin-logo-badge">
            <Zap size={22} className="text-white" />
          </div>
          <div className="admin-title-wrap">
            <div className="admin-title">
              <span>Smart Canteen</span>
              <span style={{ fontSize: '0.825rem', fontWeight: 700, color: 'var(--accent-cyan)', background: 'rgba(6, 182, 212, 0.15)', padding: '0.15rem 0.55rem', borderRadius: 'var(--radius-full)', border: '1px solid rgba(6, 182, 212, 0.3)' }}>Executive Suite</span>
            </div>
            <div className="admin-subtitle">
              <span className="live-beacon"></span>
              <span>AI Multi-Modal Biometrics & Payroll Hub</span>
            </div>
          </div>
        </div>

        {/* Navigation Tabs with True URL Routing */}
        <nav className="admin-nav">
          <button 
            className={`nav-tab ${currentPath.startsWith('/employees') ? 'active' : ''}`}
            onClick={() => navigate('/employees')}
          >
            <Users size={15} /> 
            <span>Employees</span>
            <span className="nav-tab-badge">{safeEmployees.length}</span>
          </button>
          <button 
            className={`nav-tab ${currentPath.startsWith('/transactions') ? 'active' : ''}`}
            onClick={() => navigate('/transactions')}
          >
            <Receipt size={15} /> 
            <span>Transactions</span>
            <span className="nav-tab-badge">{safeTxs.length}</span>
          </button>
          <button 
            className={`nav-tab ${currentPath.startsWith('/biometrics') || currentPath.startsWith('/faces') ? 'active' : ''}`}
            onClick={() => navigate('/biometrics')}
          >
            <Camera size={15} /> 
            <span>Biometrics</span>
            <span className="nav-tab-badge">{safeFaces.length}</span>
          </button>
          <button 
            className={`nav-tab ${currentPath.startsWith('/menu') || currentPath.startsWith('/pricing') ? 'active' : ''}`}
            onClick={() => navigate('/menu')}
          >
            <Utensils size={15} /> 
            <span>Menu & Prices</span>
            <span className="nav-tab-badge">{safeFoods.length}</span>
          </button>
          <button 
            className={`nav-tab ${currentPath.startsWith('/recommendations') || currentPath.startsWith('/wellness') ? 'active' : ''}`}
            onClick={() => navigate('/recommendations')}
          >
            <Sparkles size={15} /> 
            <span>AI Nutrition</span>
          </button>
          <button 
            className={`nav-tab ${currentPath.startsWith('/benchmarks') ? 'active' : ''}`}
            onClick={() => navigate('/benchmarks')}
          >
            <Gauge size={15} /> 
            <span>Benchmarks</span>
          </button>
        </nav>

        {/* Top Actions & Theme Toggle */}
        <div style={{ display: 'flex', gap: '0.65rem', alignItems: 'center' }}>
          {/* Light / Dark Mode Toggle Button */}
          <button 
            className="theme-toggle-btn"
            onClick={toggleTheme}
            title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            aria-label="Toggle Theme Mode"
          >
            {theme === 'dark' ? (
              <span style={{ fontSize: '1.1rem' }}>☀️</span>
            ) : (
              <span style={{ fontSize: '1.1rem' }}>🌙</span>
            )}
          </button>

          <button className="btn btn-primary" onClick={() => setIsRegisterOpen(true)}>
            <Plus size={16} /> Register Employee & Face
          </button>
          <a 
            href="http://localhost:5173" 
            target="_blank" 
            rel="noreferrer" 
            className="btn btn-outline" 
            style={{ padding: '0.45rem 0.85rem', fontSize: '0.8rem' }}
          >
            <ExternalLink size={14} /> Open POS Kiosk
          </a>
        </div>
      </header>

      {/* Main Admin Content Container with React Router */}
      <main className="admin-container">
        {fetchError && (
          <div style={{ background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#fda4af', padding: '1rem', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <AlertCircle size={20} />
            <div>
              <strong>Backend Connection Notice:</strong> {fetchError}. Please ensure backend is running at <code>http://localhost:8000</code>.
            </div>
          </div>
        )}

        {/* Routes */}
        <Routes>
          <Route path="/" element={<Navigate to="/transactions" replace />} />
          <Route 
            path="/employees" 
            element={
              <EmployeeDirectory
                employees={safeEmployees}
                onRefresh={fetchData}
                onOpenRegister={() => setIsRegisterOpen(true)}
              />
            } 
          />
          <Route 
            path="/transactions" 
            element={
              <TransactionLedger
                transactions={safeTxs}
                analytics={analytics}
                onRefresh={fetchData}
              />
            } 
          />
          <Route 
            path="/biometrics" 
            element={
              <FaceGallery
                enrolledFaces={safeFaces}
                onDeactivate={handleDeactivateFace}
                onRefresh={fetchData}
              />
            } 
          />
          <Route path="/faces" element={<Navigate to="/biometrics" replace />} />
          <Route 
            path="/menu" 
            element={
              <MenuPricingCatalog
                foods={safeFoods}
                onRefresh={fetchData}
              />
            } 
          />
          <Route path="/pricing" element={<Navigate to="/menu" replace />} />
          <Route 
            path="/recommendations" 
            element={
              <RecommendationInsights
                employees={safeEmployees}
                onRefresh={fetchData}
              />
            } 
          />
          <Route path="/wellness" element={<Navigate to="/recommendations" replace />} />
          <Route 
            path="/benchmarks" 
            element={<BenchmarkEvaluator />} 
          />
          <Route path="*" element={<Navigate to="/transactions" replace />} />
        </Routes>
      </main>

      {/* Unified All-in-One Registration Modal */}
      <UnifiedRegisterModal
        isOpen={isRegisterOpen}
        onClose={() => setIsRegisterOpen(false)}
        onSuccess={() => {
          fetchData();
        }}
      />
    </div>
  );
}
