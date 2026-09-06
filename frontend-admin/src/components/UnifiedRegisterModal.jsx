import React, { useState } from 'react';
import { 
  X, Upload, UserPlus, Camera, Sparkles, AlertCircle, CheckCircle, 
  Activity, Heart, ShieldCheck, Check, ArrowRight, UserCheck
} from 'lucide-react';
import { employeeApi, faceApi } from '../services/api';

export default function UnifiedRegisterModal({ isOpen, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    employee_code: '',
    first_name: '',
    last_name: '',
    department: 'Engineering',
    email: '',
    age: 26,
    height_cm: 175,
    weight_kg: 70,
    daily_calorie_target: 2200,
    diet_type: 'normal',
    health_goal: 'maintain',
    notes: '',
  });

  const [faceFile, setFaceFile] = useState(null);
  const [facePreview, setFacePreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  if (!isOpen) return null;

  // Real-time BMI calculation
  const heightM = Number(formData.height_cm) / 100;
  const bmi = heightM > 0 ? (Number(formData.weight_kg) / (heightM * heightM)).toFixed(1) : 0;
  let bmiCategory = 'Normal weight';
  if (bmi < 18.5) bmiCategory = 'Underweight';
  else if (bmi >= 25 && bmi < 30) bmiCategory = 'Overweight';
  else if (bmi >= 30) bmiCategory = 'Obese';

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: ['age', 'height_cm', 'weight_kg', 'daily_calorie_target'].includes(name)
        ? Number(value)
        : value,
    }));
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setFaceFile(file);
      setFacePreview(URL.createObjectURL(file));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);

    try {
      const code = formData.employee_code.toUpperCase().trim();
      const fName = formData.first_name.trim();
      const lName = formData.last_name.trim();
      const email = formData.email.trim();

      if (!code || !fName || !lName || !email) {
        throw new Error('Please fill in Employee Code, First Name, Last Name, and Email.');
      }

      // Step 1: Create Employee Core Entity
      const empResult = await employeeApi.create({
        employee_code: code,
        first_name: fName,
        last_name: lName,
        department: formData.department,
        email: email,
        active: true,
      });

      const empId = empResult?.id || empResult?.employee?.id;

      // Step 2: Create / Initialize Nutrition & Biometric Health Profile
      if (empId) {
        try {
          await employeeApi.createProfile(empId, {
            age: Number(formData.age) || 25,
            height_cm: Number(formData.height_cm),
            weight_kg: Number(formData.weight_kg),
            daily_calorie_target: Number(formData.daily_calorie_target) || 2200,
            diet_type: formData.diet_type,
            health_goal: formData.health_goal,
            notes: formData.notes || '',
          });
        } catch (profileErr) {
          console.warn('Profile init warning:', profileErr);
        }
      }

      // Step 3: If face photo provided, extract & register 128D SFace Biometric Vector
      if (faceFile) {
        const faceFormData = new FormData();
        faceFormData.append('file', faceFile);
        faceFormData.append('employee_code', code);
        faceFormData.append('sample_tag', 'frontal');
        await faceApi.register(faceFormData);
      }

      setSuccess(`Employee ${fName} ${lName} (${code}) and Biometrics successfully registered!`);
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1200);
    } catch (err) {
      console.error('Registration Error:', err);
      setError(err.message || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" style={{ maxWidth: '720px' }} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="card-header-flex" style={{ margin: 0, paddingBottom: '0.85rem' }}>
          <div className="card-title-lg">
            <UserPlus className="text-purple" size={22} />
            <span>Register Employee & SFace Biometrics</span>
          </div>
          <button className="btn btn-outline" style={{ padding: '0.3rem 0.55rem' }} onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        {error && (
          <div style={{ background: 'rgba(244, 63, 94, 0.12)', border: '1px solid rgba(244, 63, 94, 0.3)', color: 'var(--accent-rose)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', marginTop: '1rem', fontSize: '0.85rem' }}>
            ⚠️ <strong>Error:</strong> {error}
          </div>
        )}

        {success && (
          <div style={{ background: 'rgba(16, 185, 129, 0.12)', border: '1px solid rgba(16, 185, 129, 0.3)', color: 'var(--accent-emerald)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', marginTop: '1rem', fontSize: '0.85rem' }}>
            ✓ {success}
          </div>
        )}

        <form onSubmit={handleSubmit} className="form-grid">
          {/* Section 1: Basic Information */}
          <div className="form-group">
            <label className="form-label">Employee Code *</label>
            <input
              type="text"
              name="employee_code"
              placeholder="e.g. EMP2026"
              value={formData.employee_code}
              onChange={handleChange}
              className="form-input"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Department</label>
            <select name="department" value={formData.department} onChange={handleChange} className="form-select">
              <option value="Engineering">Engineering</option>
              <option value="IT / Engineering">IT / Engineering</option>
              <option value="Finance & Accounting">Finance & Accounting</option>
              <option value="Operations">Operations</option>
              <option value="Human Resources">Human Resources</option>
              <option value="Marketing">Marketing</option>
              <option value="Executive">Executive</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">First Name *</label>
            <input
              type="text"
              name="first_name"
              placeholder="e.g. Pasindu"
              value={formData.first_name}
              onChange={handleChange}
              className="form-input"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Last Name *</label>
            <input
              type="text"
              name="last_name"
              placeholder="e.g. Lakmal"
              value={formData.last_name}
              onChange={handleChange}
              className="form-input"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Email Address *</label>
            <input
              type="email"
              name="email"
              placeholder="e.g. pasindu@company.com"
              value={formData.email}
              onChange={handleChange}
              className="form-input"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Age (Years)</label>
            <input
              type="number"
              name="age"
              value={formData.age}
              onChange={handleChange}
              className="form-input"
              min="16"
              max="100"
            />
          </div>

          {/* Section 2: Health & Dietary Profile */}
          <div className="form-group">
            <label className="form-label">Height (cm)</label>
            <input
              type="number"
              name="height_cm"
              value={formData.height_cm}
              onChange={handleChange}
              className="form-input"
              min="100"
              max="250"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Weight (kg)</label>
            <input
              type="number"
              name="weight_kg"
              value={formData.weight_kg}
              onChange={handleChange}
              className="form-input"
              min="30"
              max="250"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Daily Calorie Target (kcal)</label>
            <input
              type="number"
              name="daily_calorie_target"
              value={formData.daily_calorie_target}
              onChange={handleChange}
              className="form-input"
              min="1000"
              max="5000"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Dietary Preference</label>
            <select name="diet_type" value={formData.diet_type} onChange={handleChange} className="form-select">
              <option value="normal">Standard (Normal)</option>
              <option value="vegetarian">Vegetarian</option>
              <option value="vegan">Vegan</option>
              <option value="pescatarian">Pescatarian</option>
              <option value="halal">Halal</option>
              <option value="diabetic">Diabetic Friendly</option>
            </select>
          </div>

          <div className="form-group full-width">
            <label className="form-label">Dietary Notes & Allergens (Optional)</label>
            <input
              type="text"
              name="notes"
              placeholder="e.g. No Beef, Low Sodium, Peanut Allergy"
              value={formData.notes}
              onChange={handleChange}
              className="form-input"
            />
          </div>

          {/* BMI Live Preview Box */}
          <div className="form-group full-width" style={{ background: 'var(--tile-bg)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', border: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>WHO Calculated BMI Index:</span>
            <span style={{ fontWeight: 800, color: 'var(--accent-emerald)', fontSize: '0.95rem' }}>
              {bmi} ({bmiCategory})
            </span>
          </div>

          {/* Section 3: Face Biometrics Upload */}
          <div className="form-group full-width">
            <label className="form-label">Employee Face Photo (Auto-extracts 128D SFace Biometric Vector)</label>
            <label className="dropzone" style={{ display: 'block', padding: '1.25rem' }}>
              <input type="file" accept="image/*" onChange={handleFileChange} style={{ display: 'none' }} />
              {facePreview ? (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '1rem' }}>
                  <img src={facePreview} alt="Face Preview" style={{ width: '64px', height: '64px', borderRadius: 'var(--radius-sm)', objectFit: 'cover', border: '2px solid var(--accent-purple)' }} />
                  <div style={{ textAlign: 'left' }}>
                    <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-primary)' }}>Biometric Sample Loaded</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--accent-emerald)', fontWeight: 600 }}>✓ Ready for 128D SFace Feature Vector Extraction</div>
                  </div>
                </div>
              ) : (
                <div style={{ color: 'var(--text-muted)' }}>
                  <Camera size={28} className="text-purple" style={{ margin: '0 auto 0.4rem auto' }} />
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>Click to Browse or Drop Employee Face Image</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.2rem' }}>Supports JPG, PNG with clear frontal lighting</div>
                </div>
              )}
            </label>
          </div>

          {/* Submit Actions */}
          <div className="form-group full-width" style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.85rem' }}>
            <button type="button" className="btn btn-outline" onClick={onClose} disabled={loading}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              <UserPlus size={16} />
              {loading ? 'Generating 128D Embeddings...' : 'Register Employee & Biometrics'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
