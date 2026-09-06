import React, { useState, useRef } from 'react';
import { Camera, UserCheck, Upload, AlertCircle, RefreshCw, Sparkles } from 'lucide-react';

export default function FaceScanner({ onFaceRecognized, isScanning, onReset, currentMatch }) {
  const [preview, setPreview] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setPreview(url);
      onFaceRecognized(file, url);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      const url = URL.createObjectURL(file);
      setPreview(url);
      onFaceRecognized(file, url);
    }
  };

  const handleReset = (e) => {
    e.stopPropagation();
    setPreview(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    onReset();
  };

  return (
    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="card-header">
        <div className="card-title">
          <Camera className="text-cyan" size={20} />
          <span>Biometric Face Scanner</span>
        </div>
        {preview && (
          <button className="btn btn-outline" style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }} onClick={handleReset}>
            <RefreshCw size={12} /> Clear
          </button>
        )}
      </div>

      <div 
        className={`scanner-box ${currentMatch ? 'active' : ''}`}
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

        {preview ? (
          <>
            <img src={preview} alt="Face Scan Preview" className="scanner-preview" />
            <div className="scanner-overlay-badge">
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                {isScanning ? <RefreshCw className="spin text-cyan" size={14} /> : <UserCheck className="text-emerald" size={14} />}
                {isScanning ? 'Extracting 128D Embedding...' : (currentMatch?.matched ? 'Face Verified' : 'Face Scanned')}
              </span>
              <span className="text-cyan">{currentMatch?.matched ? `${(currentMatch.confidence * 100).toFixed(0)}% Match` : ''}</span>
            </div>
          </>
        ) : (
          <>
            <div className="scanner-icon">
              <Camera size={26} />
            </div>
            <div className="scanner-title">Click or Drop Face Photo</div>
            <div className="scanner-desc">Instant 128D SFace Biometric Match</div>
          </>
        )}
      </div>

      <div style={{ marginTop: '0.75rem', fontSize: '0.75rem', color: 'var(--text-dim)', textAlign: 'center' }}>
        📷 Tap box to open camera/upload employee face photo
      </div>
    </div>
  );
}
