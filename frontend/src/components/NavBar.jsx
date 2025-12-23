import { NavLink, useNavigate } from 'react-router-dom';

import useAuth from '../hooks/useAuth.js';

function NavBar() {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="navbar">
      <div>
        <strong>Emociones IA</strong>
      </div>
      <nav className="navbar-links">
        {isAuthenticated ? (
          <>
            <NavLink className="nav-link" to="/media-lab">
              Media Lab
            </NavLink>
            <NavLink className="nav-link" to="/dashboard-emociones">
              Dashboard emociones
            </NavLink>
            <button className="nav-link" style={{ border: 'none', background: 'transparent', cursor: 'pointer' }} onClick={handleLogout}>
              Salir {user?.full_name?.split(' ')[0] || ''}
            </button>
          </>
        ) : (
          <>
            <NavLink className="nav-link" to="/login">
              Login
            </NavLink>
            <NavLink className="nav-link" to="/register">
              Registro
            </NavLink>
          </>
        )}
      </nav>
    </header>
  );
}

export default NavBar;
