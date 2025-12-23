import { Navigate, Route, Routes } from 'react-router-dom';

import NavBar from './components/NavBar.jsx';
import ProtectedRoute from './components/ProtectedRoute.jsx';
import Login from './pages/Login.jsx';
import MediaLab from './pages/MediaLab.jsx';
import Register from './pages/Register.jsx';
import TextAnalyzer from './pages/TextAnalyzer.jsx';
import Dashboard from './pages/Dashboard.jsx';
import useAuth from './hooks/useAuth.js';

function App() {
  const { isAuthenticated } = useAuth();

  return (
    <div>
      <NavBar />
      <Routes>
        <Route path="/" element={<Navigate to={isAuthenticated ? '/analyze' : '/login'} replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/analyze"
          element={
            <ProtectedRoute>
              <MediaLab />
            </ProtectedRoute>
          }
        />
        <Route
          path="/media-lab"
          element={
            <ProtectedRoute>
              <MediaLab />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard-emociones"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard"
          element={<Navigate to="/dashboard-emociones" replace />}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}

export default App;
