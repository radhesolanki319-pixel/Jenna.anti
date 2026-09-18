'use client';

import { type ReactNode } from 'react';
import { usePathname } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import { useAuth } from '@/components/providers/AuthProvider';

export function DashboardLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { user, isLoading } = useAuth();

  const isAuthRoute = pathname === '/login' || pathname === '/register';

  if (isAuthRoute) {
    return (
      <div className="flex min-h-screen bg-[#07090e] text-foreground flex-col justify-center">
        {children}
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#07090e] text-white">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-cyan-400" />
          <p className="text-sm text-zinc-400 font-medium">Loading session...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null; // AuthProvider redirect hook will forward to /login
  }

  return (
    <div className="h-[100dvh] w-full max-w-full overflow-hidden bg-[#07090e] text-white flex flex-col">
      {children}
    </div>
  );
}
