import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { faceApi, mealApi, employeeApi, recommendationApi } from './services/api';
import FaceScanner from './components/FaceScanner';
import PlateScanner from './components/PlateScanner';
import IdentityBadge from './components/IdentityBadge';
import CalorieGauge from './components/CalorieGauge';
import ItemizedReceipt from './components/ItemizedReceipt';
import MealHistoryModal from './components/MealHistoryModal';
import PersonalizedRecommendationBox from './components/PersonalizedRecommendationBox';
import { Sparkles, Shield, ExternalLink, RefreshCw, Clock, Flame, Zap } from 'lucide-react';

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();

  const [faceFile, setFaceFile] = useState(null);
  const [facePreview, setFacePreview] = useState(null);
  const [isFaceScanning, setIsFaceScanning] = useState(false);
  const [faceMatch, setFaceMatch] = useState(null);
  const [employeeProfile, setEmployeeProfile] = useState(null);

  const [plateFile, setPlateFile] = useState(null);
  const [platePreview, setPlatePreview] = useState(null);
  const [isPlateAnalyzing, setIsPlateAnalyzing] = useState(false);
  const [mealResult, setMealResult] = useState(null);

  const [recommendation, setRecommendation] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [timeStr, setTimeStr] = useState('');

  // Live Counter Clock
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Fetch Phase 6 Recommendations Helper
  const fetchRecommendations = async (empCode, items = null) => {
    if (!empCode) return;
    try {
      const itemsPayload = items ? items.map((it) => ({
        food_name: it.food_name,
        quantity: it.quantity || 1,
      })) : null;
      const rec = await recommendationApi.getPersonalized(empCode, itemsPayload);
      setRecommendation(rec);
    } catch (recErr) {
      console.warn('Recommendation fetch warning:', recErr);
    }
  };

  // Handle Face Recognition
  const handleFaceRecognized = async (file, previewUrl) => {
    setFaceFile(file);
    setFacePreview(previewUrl);
    setIsFaceScanning(true);
    setErrorMessage(null);

    try {
      const match = await faceApi.recognize(file);
      setFaceMatch(match);

      if (match.matched && match.employee_code) {
        // Fetch full health & nutrition profile
        const profile = await employeeApi.getProfile(match.employee_code);
        setEmployeeProfile(profile);

        // Fetch Phase 6 Personalized Recommendation
        await fetchRecommendations(match.employee_code, mealResult?.items || null);
      } else {
        setEmployeeProfile(null);
        setRecommendation(null);
      }
    } catch (err) {
      console.error('Face error:', err);
      setErrorMessage(err.message || 'Face recognition service error.');
      setFaceMatch({ matched: false });
      setRecommendation(null);
    } finally {
      setIsFaceScanning(false);
    }
  };

  // Handle Food Plate Analysis
  const handlePlateAnalyzed = async (file, previewUrl) => {
    setPlateFile(file);
    setPlatePreview(previewUrl);
    setIsPlateAnalyzing(true);
    setErrorMessage(null);

    try {
      const res = await mealApi.analyze(file);
      setMealResult(res);

      // Re-evaluate recommendations with scanned plate
      if (faceMatch?.matched && faceMatch?.employee_code) {
        await fetchRecommendations(faceMatch.employee_code, res?.items || null);
      }
    } catch (err) {
      console.error('Plate analysis error:', err);
      setErrorMessage(err.message || 'Food plate YOLO analysis error.');
    } finally {
      setIsPlateAnalyzing(false);
    }
  };

  const handleResetFace = () => {
    setFaceFile(null);
    setFacePreview(null);
    setFaceMatch(null);
    setEmployeeProfile(null);
    setRecommendation(null);
  };

  const handleResetPlate = () => {
    setPlateFile(null);
    setPlatePreview(null);
    setMealResult(null);
    if (faceMatch?.matched && faceMatch?.employee_code) {
      fetchRecommendations(faceMatch.employee_code, null);
    }
  };

  const handleResetAll = () => {
    handleResetFace();
    handleResetPlate();
    setErrorMessage(null);
    setRecommendation(null);
  };

  const [theme, setTheme] = useState(() => localStorage.getItem('canteen_theme') || 'dark');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('canteen_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const activeEmpCode = employeeProfile?.employee_code || faceMatch?.employee_code;
  const activeEmpName = employeeProfile?.name || `${employeeProfile?.first_name || ''} ${employeeProfile?.last_name || ''}`.trim() || faceMatch?.employee_name || 'Employee';

  const isHistoryOpen = location.pathname.startsWith('/history');

  return (
    <div className="kiosk-app">
      {/* Top Header */}
      <header className="kiosk-header">
        <div className="brand-section">
          <div className="brand-icon">
            <Zap size={22} className="text-white" />
          </div>
          <div>
            <div className="brand-title">
              <span>Smart Canteen</span>
              <span style={{ fontSize: '0.825rem', fontWeight: 700, color: 'var(--accent-cyan)', background: 'rgba(6, 182, 212, 0.15)', padding: '0.15rem 0.55rem', borderRadius: 'var(--radius-full)', border: '1px solid rgba(6, 182, 212, 0.3)', marginLeft: '0.5rem' }}>AI POS Counter</span>
            </div>
            <div className="brand-subtitle">
              <span className="live-indicator"></span>
              <span>Live Multi-Modal AI Counter • Counter #01</span>
            </div>
          </div>
        </div>

        <div className="header-actions">
          <div className="action-badge" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>
            <Clock size={14} className="text-orange" />
            <span>{timeStr || '12:00:00 PM'}</span>
          </div>

          <div className="action-badge">
            <Shield size={14} className="text-cyan" />
            <span>SFace Biometrics Active</span>
          </div>

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

          <a 
            href="http://localhost:5174" 
            target="_blank" 
            rel="noreferrer" 
            className="btn btn-outline" 
            style={{ padding: '0.45rem 0.9rem', fontSize: '0.8rem' }}
          >
            <ExternalLink size={14} /> Open Admin Portal
          </a>
        </div>
      </header>

      {/* Main Kiosk POS Content */}
      <main className="kiosk-grid">
        {/* Left Column: Dual Scanners & Employee Info & Recommendations */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {errorMessage && (
            <div style={{ background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#fda4af', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', fontSize: '0.85rem' }}>
              ⚠️ {errorMessage}
            </div>
          )}

          {/* Dual Camera Scanner Blocks */}
          <div className="scanners-container">
            <FaceScanner 
              onFaceRecognized={handleFaceRecognized}
              isScanning={isFaceScanning}
              onReset={handleResetFace}
              currentMatch={faceMatch}
            />

            <PlateScanner 
              onPlateAnalyzed={handlePlateAnalyzed}
              isAnalyzing={isPlateAnalyzing}
              onReset={handleResetPlate}
              mealResult={mealResult}
            />
          </div>

          {/* Employee Identity & Health Goals Card */}
          <IdentityBadge 
            employee={employeeProfile}
            matchInfo={faceMatch}
            facePreviewUrl={facePreview}
            onViewHistory={activeEmpCode ? () => navigate('/history') : null}
          />

          {/* Calorie Gauge Progress */}
          {mealResult && (
            <CalorieGauge 
              mealCalories={mealResult.meal_totals?.calories_kcal || mealResult.total_calories || 0}
              dailyTarget={employeeProfile?.profile?.daily_calorie_target || 2200}
            />
          )}

          {/* Phase 6: Personalized Recommendation Box */}
          <PersonalizedRecommendationBox 
            recommendation={recommendation}
          />
        </div>

        {/* Right Column: Itemized POS Receipt & Nutrition Breakdown */}
        <div>
          <ItemizedReceipt 
            mealResult={mealResult}
            employee={employeeProfile}
            onResetAll={handleResetAll}
          />
        </div>
      </main>

      {/* Personal Meal History & Nutrition Log Modal with URL Sync */}
      <MealHistoryModal
        isOpen={isHistoryOpen}
        onClose={() => navigate('/')}
        employeeCode={activeEmpCode || 'EMP001'}
        employeeName={activeEmpName || 'Staff Member'}
      />
    </div>
  );
}
