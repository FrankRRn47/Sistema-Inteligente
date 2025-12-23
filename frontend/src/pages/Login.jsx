import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import useAuth from '../hooks/useAuth.js';
import { loginUser } from '../services/authService.js';

function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);
    try {
      const response = await loginUser(form);
      login(response.token, response.user);
      navigate('/analyze');
    } catch (err) {
      setError(err.response?.data?.message || err.message || 'Credenciales inválidas.');
    } finally {
      setLoading(false);
    }
  };

    return (
      <div className="auth-flex-row">
        <form onSubmit={handleSubmit} className="auth-card">
          <div className="form-group">
            <label htmlFor="email" style={{ fontWeight: 500, color: '#3b3b5c' }}>Correo</label>
            <input id="email" name="email" type="email" value={form.email} onChange={handleChange} required style={{ fontWeight: 600, fontSize: '1.05rem', background: '#f7f7fa', border: '1px solid #e0e7ff', borderRadius: '0.75rem', padding: '0.8rem 1rem', marginTop: '0.2rem' }} />
          </div>
          <div className="form-group">
            <label htmlFor="password" style={{ fontWeight: 500, color: '#3b3b5c' }}>Contraseña</label>
            <input id="password" name="password" type="password" value={form.password} onChange={handleChange} required style={{ fontWeight: 600, fontSize: '1.05rem', background: '#f7f7fa', border: '1px solid #e0e7ff', borderRadius: '0.75rem', padding: '0.8rem 1rem', marginTop: '0.2rem' }} />
          </div>
          {error && <p style={{ color: 'crimson', fontWeight: 500 }}>{error}</p>}
          <button className="primary-btn" type="submit" disabled={loading} style={{ fontWeight: 600, fontSize: '1.08rem', borderRadius: '0.75rem', padding: '0.9rem 0' }}>
            {loading ? 'Ingresando...' : 'Entrar'}
          </button>
          <p style={{ textAlign: 'center', marginTop: '0.5rem', color: '#6b7280' }}>
            ¿Nuevo usuario? <Link to="/register">Crea una cuenta</Link>
          </p>
        </form>
        <div className="auth-side-card login">
          <img src="/account_logo.svg" alt="Acceder cuenta" style={{ width: 80, height: 80, marginBottom: '1.2rem' }} />
          <h3 style={{ color: '#3b3b5c', fontWeight: 600, fontSize: '1.1rem', textAlign: 'center', marginBottom: '0.7rem' }}>Inicie sesión y descubra sus emociones</h3>
          <p style={{ color: '#7c3aed', fontWeight: 400, fontSize: '1rem', textAlign: 'center', margin: 0 }}>
            "Tus emociones son el inicio de tu autoconocimiento."
          </p>
        </div>
      </div>
    );
}

export default Login;
