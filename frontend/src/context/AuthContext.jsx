import { createContext, useEffect, useMemo, useState } from 'react';

export const AuthContext = createContext(null);

const TOKEN_KEY = 'ia_dashboard_token';
const USER_KEY = 'ia_dashboard_user';

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem(USER_KEY);
    return stored ? JSON.parse(stored) : null;
  });

  useEffect(() => {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  }, [token]);

  useEffect(() => {
    if (user) {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    } else {
      localStorage.removeItem(USER_KEY);
    }
  }, [user]);

  const value = useMemo(
    () => ({
      token,
      user,
      isAuthenticated: Boolean(token),
      login: (nextToken, nextUser) => {
        setToken(nextToken);
        setUser(nextUser);
      },
      logout: () => {
        setToken(null);
        setUser(null);
      },
      updateUser: (partial) => setUser((prev) => (prev ? { ...prev, ...partial } : prev)),
    }),
    [token, user]
  );

  useEffect(() => {
    const handler = () => {
      setToken(null);
      setUser(null);
    };
    window.addEventListener('auth:unauthorized', handler);
    return () => window.removeEventListener('auth:unauthorized', handler);
  }, []);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
