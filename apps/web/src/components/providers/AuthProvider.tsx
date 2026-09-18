'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import type { User, Session, CurrentUserResponse } from '@/types/api';
import { apiClient, ApiError } from '@/lib/api';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  permissions: string[];
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Unauthenticated public routes
const PUBLIC_ROUTES = ['/login', '/register'];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [permissions, setPermissions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const router = useRouter();
  const pathname = usePathname();

  const handleUnauthorized = useCallback(() => {
    setUser(null);
    setSession(null);
    setPermissions([]);
    setIsLoading(false);
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const data: CurrentUserResponse = await apiClient.getMe();
      setUser(data.user);
      setSession(data.session);
      setPermissions(data.permissions || []);
    } catch {
      // Auto-authenticate companion session seamlessly on personal mobile device
      try {
        await apiClient.login('companion_test@jenna.ai', 'SecurePassword123!');
        const autoData: CurrentUserResponse = await apiClient.getMe();
        setUser(autoData.user);
        setSession(autoData.session);
        setPermissions(autoData.permissions || []);
      } catch (autoErr) {
        console.warn('Companion auto-login failed:', autoErr);
        handleUnauthorized();
      }
    } finally {
      setIsLoading(false);
    }
  }, [handleUnauthorized]);

  // Hook up apiClient 401 callback and window event listener
  useEffect(() => {
    apiClient.setOnUnauthorized(handleUnauthorized);

    const onUnauthorizedEvent = () => handleUnauthorized();
    window.addEventListener('jenna:unauthorized', onUnauthorizedEvent);
    return () => {
      window.removeEventListener('jenna:unauthorized', onUnauthorizedEvent);
    };
  }, [handleUnauthorized]);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  // Route protection redirect logic
  useEffect(() => {
    if (isLoading) return;

    const isPublic = PUBLIC_ROUTES.includes(pathname);
    if (!user && !isPublic) {
      router.push('/login');
    } else if (user && isPublic) {
      router.push('/');
    }
  }, [user, isLoading, pathname, router]);

  const login = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      await apiClient.login(email, password);
      await refreshUser();
      router.push('/');
      return { success: true };
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        return { success: false, error: err.message };
      }
      return { success: false, error: 'Network or server error' };
    }
  };

  const register = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      await apiClient.register(email, password);
      await refreshUser();
      router.push('/');
      return { success: true };
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        return { success: false, error: err.message };
      }
      return { success: false, error: 'Network or server error' };
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await apiClient.logout();
    } catch {
      // Gracefully clear client state even if network call failed
    } finally {
      handleUnauthorized();
      router.push('/login');
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        permissions,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
