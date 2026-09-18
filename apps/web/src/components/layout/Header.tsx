'use client';

import { Menu, ShieldCheck, LogOut, User as UserIcon, Radio, Wifi, WifiOff } from 'lucide-react';
import { useAuth } from '@/components/providers/AuthProvider';
import { useWebSocketContext } from '@/components/providers/WebSocketProvider';
import { ThemeToggle } from './ThemeToggle';

interface HeaderProps {
  onMenuToggle: () => void;
}

export function Header({ onMenuToggle }: HeaderProps) {
  const { user, logout } = useAuth();
  const { status: wsStatus, latencyMs, reconnect } = useWebSocketContext();

  const isWsConnected = wsStatus === 'connected';
  const isWsReconnecting = wsStatus === 'reconnecting' || wsStatus === 'connecting';

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-border bg-card/80 px-4 sm:px-6 backdrop-blur-sm">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuToggle}
          className="rounded-lg p-2 text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 lg:hidden dark:text-zinc-400 dark:hover:bg-zinc-800"
          aria-label="Toggle navigation menu"
        >
          <Menu className="h-5 w-5" />
        </button>
        <div className="flex items-center gap-2 text-xs font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
          <ShieldCheck className="h-3.5 w-3.5" />
          <span>Jenna Control Center</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* WebSocket Realtime Status Indicator */}
        <button
          onClick={() => {
            if (!isWsConnected) reconnect();
          }}
          title={isWsConnected ? 'WebSocket live heartbeat active' : 'Click to reconnect WebSocket'}
          className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium border transition-colors ${
            isWsConnected
              ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20'
              : isWsReconnecting
              ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20 animate-pulse'
              : 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20 hover:bg-rose-500/20 cursor-pointer'
          }`}
        >
          {isWsConnected ? (
            <Wifi className="h-3 w-3" />
          ) : isWsReconnecting ? (
            <Radio className="h-3 w-3 animate-spin" />
          ) : (
            <WifiOff className="h-3 w-3" />
          )}
          <span className="hidden sm:inline">
            {isWsConnected ? (latencyMs !== null ? `WS ${latencyMs}ms` : 'WS Live') : isWsReconnecting ? 'WS Connecting' : 'WS Offline (Retry)'}
          </span>
        </button>

        {user && (
          <div className="flex items-center gap-2 border-r border-border pr-3">
            <div className="flex items-center gap-2 rounded-full bg-zinc-100 dark:bg-zinc-800 px-3 py-1 text-xs text-foreground">
              <UserIcon className="h-3.5 w-3.5 text-zinc-400" />
              <span className="font-medium max-w-[140px] truncate">{user.email}</span>
              <span className="rounded bg-primary-500/15 px-1.5 py-0.5 text-[10px] font-semibold text-primary-600 dark:text-primary-400 uppercase">
                {user.role}
              </span>
            </div>
            <button
              onClick={() => logout()}
              title="Sign Out"
              className="rounded-lg p-2 text-zinc-500 hover:bg-red-500/10 hover:text-red-600 dark:text-zinc-400 dark:hover:bg-red-500/10 dark:hover:text-red-400 transition-colors"
              aria-label="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        )}
        <ThemeToggle />
      </div>
    </header>
  );
}
