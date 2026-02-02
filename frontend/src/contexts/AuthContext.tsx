import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { auth } from '../lib/api';
import type { User } from '../lib/api/types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

// Create context with undefined default (we'll always use it inside AuthProvider)
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Provider component that wraps the app
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // On mount: check if token exists in localStorage
  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token');
    if (storedToken) {
      // If token exists, fetch user info
      fetchUserInfo(storedToken);
    } else {
      setLoading(false);
    }
  }, []);

  // Fetch current user info from backend
  const fetchUserInfo = async (authToken: string) => {
    try {
      // Use our API client to get user info
      const userData = await auth.getCurrentUser();
      setUser(userData);
      setToken(authToken);
    } catch (error) {
      console.error('Failed to fetch user info:', error);
      // Token is invalid, clear it
      localStorage.removeItem('auth_token');
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  // Login: store token and fetch user info
  const login = async (newToken: string) => {
    localStorage.setItem('auth_token', newToken);
    setToken(newToken);
    await fetchUserInfo(newToken);
  };

  // Logout: clear everything
  const logout = () => {
    auth.logout(); // Use API client logout
    setToken(null);
    setUser(null);
  };

  const value: AuthContextType = {
    user,
    token,
    loading,
    login,
    logout,
    isAuthenticated: !!user && !!token,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Custom hook to use auth context
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used inside AuthProvider');
  }
  return context;
}
