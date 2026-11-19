import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { TOKEN_STORAGE_KEY } from '../services/api';
import { authApi } from '../services/auth';
import { notificationsApi } from '../services/notifications';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [unreadCount, setUnreadCount] = useState(0);

  const refreshUnreadCount = useCallback(async () => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!token) {
      setUnreadCount(0);
      return;
    }
    try {
      const data = await notificationsApi.list({ limit: 1 });
      setUnreadCount(data.unread_count || 0);
    } catch {
      // Non-critical background indicator fetch
    }
  }, []);

  const refreshUser = useCallback(async () => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!token) {
      setUser(null);
      setUnreadCount(0);
      setLoading(false);
      return;
    }
    try {
      const me = await authApi.getMe();
      setUser(me);
      await refreshUnreadCount();
    } catch {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      setUser(null);
      setUnreadCount(0);
    } finally {
      setLoading(false);
    }
  }, [refreshUnreadCount]);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  useEffect(() => {
    const handleUnauthorized = () => {
      setUser(null);
      setUnreadCount(0);
    };
    window.addEventListener('sprintflow:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('sprintflow:unauthorized', handleUnauthorized);
  }, []);

  const login = async (email, password) => {
    const data = await authApi.login({ email, password });
    localStorage.setItem(TOKEN_STORAGE_KEY, data.access_token);
    setUser(data.user);
    await refreshUnreadCount();
    return data.user;
  };

  const register = async (fullName, email, password) => {
    await authApi.register({ full_name: fullName, email, password });
    return login(email, password);
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setUser(null);
    setUnreadCount(0);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        setUser,
        loading,
        isAuthenticated: Boolean(user),
        unreadCount,
        setUnreadCount,
        refreshUnreadCount,
        refreshUser,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
