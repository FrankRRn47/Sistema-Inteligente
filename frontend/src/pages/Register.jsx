import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import useAuth from '../hooks/useAuth.js';
import { registerUser } from '../services/authService.js';

function Register() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [form, setForm] = useState({ full_name: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const passwordHint = 'Mínimo 8 caracteres, con una mayúscula, un número y un símbolo.';

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setFieldErrors({});
    setLoading(true);
    try {
      const response = await registerUser(form);
      login(response.token, response.user);
      navigate('/analyze');
    } catch (err) {
      setFieldErrors(err.response?.data?.errors || {});
      setError(err.response?.data?.message || err.message || 'No se pudo registrar.');
    } finally {
      setLoading(false);
    }
  };

    return (
      <div className="auth-flex-row">
        <form onSubmit={handleSubmit} className="auth-card">
          <h1 className="page-title" style={{ textAlign: 'center', marginBottom: '0.5rem', color: '#7c3aed', fontWeight: 700, fontSize: '1.4rem' }}>Crear cuenta</h1>
          <div className="form-group">
            <label htmlFor="full_name">Nombre completo</label>
            <input
              id="full_name"
              name="full_name"
              placeholder="Ej. Valeria Torres Andrade"
              value={form.full_name}
              onChange={handleChange}
              required
              aria-invalid={Boolean(fieldErrors.full_name)}
            />
            {fieldErrors.full_name && <p className="form-error">{fieldErrors.full_name}</p>}
          </div>
          <div className="form-group">
            <label htmlFor="email">Correo</label>
            <input
              id="email"
              name="email"
              type="email"
              placeholder="Ej. valeria.torres@emociones.ai"
              value={form.email}
              onChange={handleChange}
              required
              aria-invalid={Boolean(fieldErrors.email)}
            />
            {fieldErrors.email && <p className="form-error">{fieldErrors.email}</p>}
          </div>
          <div className="form-group">
            <label htmlFor="password">Contraseña</label>
            <input
              id="password"
              name="password"
              type="password"
              placeholder="Ej. EmoRadar!2025"
              value={form.password}
              onChange={handleChange}
              required
              minLength={8}
              title={passwordHint}
              autoComplete="new-password"
              aria-invalid={Boolean(fieldErrors.password)}
            />
            <small className="form-hint">{passwordHint}</small>
            {fieldErrors.password && <p className="form-error">{fieldErrors.password}</p>}
          </div>
          {error && <p style={{ color: 'crimson' }}>{error}</p>}
          <button className="primary-btn" type="submit" disabled={loading}>
            {loading ? 'Creando...' : 'Registrarme'}
          </button>
          <p style={{ textAlign: 'center', marginTop: '0.5rem' }}>
            ¿Ya tienes cuenta? <Link to="/login">Inicia sesión</Link>
          </p>
        </form>
        <div className="auth-side-card register">
          <img src="/register_logo.svg" alt="Registrarse" style={{ width: 90, height: 90, marginBottom: '1.2rem' }} />
          <h3 style={{ color: '#fff', fontWeight: 600, fontSize: '1.1rem', textAlign: 'center', marginBottom: '0.7rem' }}>Regístrate y descubramos sus emociones</h3>
          <p style={{ color: '#ede9fe', fontWeight: 400, fontSize: '1rem', textAlign: 'center', margin: 0 }}>
            "Cada emoción es una oportunidad para conocerte mejor."
          </p>
        </div>
      </div>
  );
}

export default Register;
