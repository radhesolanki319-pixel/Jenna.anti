'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  MessageSquare,
  Brain,
  Bot,
  Wrench,
  CheckSquare,
  Smartphone,
  Eye,
  Settings,
  Activity,
  Home,
  LogOut,
  User as UserIcon,
  Shield,
  FileText,
  BarChart3,
  Volume2,
} from 'lucide-react';
import { useAuth } from '@/components/providers/AuthProvider';

export interface NavItem {
  name: string;
  href: string;
  icon: any;
  active?: boolean;
  phase?: string;
}

export const navItems: NavItem[] = [
  { name: 'Home', href: '/', icon: Home, active: true },
  { name: 'Chat', href: '/chat', icon: MessageSquare, active: true },
  { name: 'Voice', href: '/voice', icon: Volume2, active: true },
  { name: 'Vision', href: '/vision', icon: Eye, active: true },
  { name: 'Memory', href: '/memory', icon: Brain, active: true },
  { name: 'Agents', href: '/agents', icon: Bot, active: true },
  { name: 'Tools', href: '/tools', icon: Wrench, active: true },
  { name: 'Tasks', href: '/tasks', icon: CheckSquare, active: true },
  { name: 'Approvals', href: '/approvals', icon: Shield, active: true },
  { name: 'Audit', href: '/audit', icon: FileText, active: true },
  { name: 'Usage', href: '/usage', icon: BarChart3, active: true },
  { name: 'Devices', href: '/devices', icon: Smartphone, active: true },
  { name: 'Settings', href: '/settings', icon: Settings, active: true },
  { name: 'System Health', href: '/health', icon: Activity, active: true },
];



interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 flex w-64 flex-col border-r border-border bg-card transition-transform duration-200 ease-in-out lg:static lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand */}
        <div className="flex h-16 items-center gap-2 border-b border-border px-6">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600 text-white font-bold">
            J
          </div>
          <div>
            <h1 className="text-base font-semibold tracking-tight">Jenna AI</h1>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">Control Center · Phase 4</p>
          </div>
        </div>

        {/* Nav Links */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={onClose}
                className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary-500/10 text-primary-600 dark:text-primary-400 font-semibold'
                    : 'text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800/60 dark:hover:text-zinc-100'
                }`}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span>{item.name}</span>
                {item.active ? (
                  <span className="ml-auto text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">
                    Live
                  </span>
                ) : (
                  <span className="ml-auto text-[10px] uppercase tracking-wider text-zinc-400 dark:text-zinc-500 border border-border rounded px-1">
                    {item.phase}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Footer info & User pill */}
        <div className="border-t border-border p-4 space-y-3">
          {user && (
            <div className="flex items-center justify-between rounded-lg bg-zinc-50 dark:bg-zinc-900/60 p-2.5 border border-border">
              <div className="flex items-center gap-2 min-w-0">
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary-500/10 text-primary-600 dark:text-primary-400">
                  <UserIcon className="h-4 w-4" />
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-medium text-foreground truncate">{user.email}</p>
                  <p className="text-[10px] uppercase font-semibold text-primary-600 dark:text-primary-400">
                    {user.role}
                  </p>
                </div>
              </div>
              <button
                onClick={() => logout()}
                title="Sign Out"
                className="rounded p-1.5 text-zinc-500 hover:bg-red-500/10 hover:text-red-600 dark:text-zinc-400 dark:hover:bg-red-500/10 dark:hover:text-red-400 transition-colors"
                aria-label="Sign out"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          )}

          <div className="rounded-md bg-zinc-50 dark:bg-zinc-900/40 p-2.5 border border-border text-[11px] text-zinc-500 dark:text-zinc-400">
            <p className="font-semibold text-zinc-700 dark:text-zinc-300">Phase 4 Active</p>
            <p className="mt-0.5">Control Center & Realtime WebSocket telemetry.</p>
          </div>
        </div>
      </aside>
    </>
  );
}
