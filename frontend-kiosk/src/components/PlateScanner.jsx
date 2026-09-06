import React, { useState, useRef } from 'react';
import { Utensils, RefreshCw, CheckCircle2, ScanLine, AlertCircle } from 'lucide-react';

export default function PlateScanner({ onPlateAnalyzed, isAnalyzing, onReset, mealResult }) {
  const [preview, setPreview] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setPreview(url);
      onPlateAnalyzed(file, url);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      const url = URL.createObjectURL(file);
      setPreview(url);
      onPlateAnalyzed(file, url);
    }
  };

  const handleReset = (e) => {
    e.stopPropagation();
    setPreview(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    onReset();
  };

  const displayImage = mealResult?.annotated_image_base64 || preview;
  const itemCount = mealResult?.items?.length || 0;
  const totalBill = mealResult?.meal_totals?.formatted_total_bill || (mealResult?.meal_totals?.total_bill_amount ? `Rs. ${mealResult.meal_totals.total_bill_amount.toFixed(2)}` : null);

  return (
    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="card-header">
        <div className="card-title">
          <Utensils className="text-orange" size={20} />
          <span>Food Plate Vision AI</span>
        </div>
        {preview && (
          <button className="btn btn-outline" style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }} onClick={handleReset}>
            <RefreshCw size={12} /> Clear
          </button>
        )}
      </div>

      <div 
        className={`scanner-box ${mealResult ? 'active' : ''}`}
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
      >
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={handleFileChange} 
          accept="image/*" 
          style={{ display: 'none' }} 
        />

        {displayImage ? (
          <>
            <img src={displayImage} alt="Plate Scan Preview" className="scanner-preview" />
            <div className="scanner-overlay-badge">
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                {isAnalyzing ? (
                  <RefreshCw className="spin text-orange" size={14} />
                ) : itemCount > 0 ? (
                  <CheckCircle2 className="text-emerald" size={14} />
                ) : (
                  <AlertCircle className="text-amber" size={14} />
                )}
                {isAnalyzing ? 'YOLO11n Multi-Class Detection...' : (itemCount > 0 ? `${itemCount} Food Items Detected` : 'No Food Detected')}
              </span>
              {totalBill && <span className="text-orange" style={{ fontWeight: 700 }}>{totalBill}</span>}
            </div>
          </>
        ) : (
          <>
            <div className="scanner-icon" style={{ background: 'rgba(249, 115, 22, 0.12)', color: 'var(--accent-orange)' }}>
              <ScanLine size={26} />
            </div>
            <div className="scanner-title">Click or Drop Food Plate</div>
            <div className="scanner-desc">YOLO11n Detection + Automated Billing</div>
          </>
        )}
      </div>

      <div style={{ marginTop: '0.75rem', fontSize: '0.75rem', color: 'var(--text-dim)', textAlign: 'center' }}>
        🍛 Tap box to scan canteen lunch plate or snacks
      </div>
    </div>
  );
}
