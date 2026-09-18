'use client';

import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, RefreshCw, Radio } from 'lucide-react';

export type BadgeStatusType =
  | 'healthy'
  | 'online'
  | 'connected'
  | 'degraded'
  | 'reconnecting'
  | 'connecting'
  | 'unhealthy'
  | 'offline'
  | 'disconnected'
  | 'error';

interface StatusBadgeProps {
  status: BadgeStatusType | string;
  label?: string;
  showDot?: boolean;
  size?: 'sm' | 'md';
}

export function StatusBadge({
  status,
  label,
  showDot = true,
  size = 'md',
}: StatusBadgeProps) {
  const normStatus = status.toLowerCase();

  let colorClasses = 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 border-zinc-200 dark:border-zinc-700';
  let dotColor = 'bg-zinc-400';
  let Icon = Radio;
  let defaultLabel = status;
  let pulse = false;

  if (normStatus === 'healthy' || normStatus === 'online' || normStatus === 'connected' || normStatus === 'ok') {
    colorClasses = 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/20';
    dotColor = 'bg-emerald-500';
    Icon = CheckCircle2;
    defaultLabel = normStatus === 'connected' ? 'Connected' : 'Healthy';
  } else if (normStatus === 'degraded' || normStatus === 'reconnecting') {
    colorClasses = 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/20';
    dotColor = 'bg-amber-500';
    Icon = AlertTriangle;
    defaultLabel = normStatus === 'reconnecting' ? 'Reconnecting' : 'Degraded';
    pulse = true;
  } else if (normStatus === 'connecting') {
    colorClasses = 'bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/20';
    dotColor = 'bg-blue-500';
    Icon = RefreshCw;
    defaultLabel = 'Connecting';
    pulse = true;
  } else if (
    normStatus === 'unhealthy' ||
    normStatus === 'offline' ||
    normStatus === 'error' ||
    normStatus === 'not_ready'
  ) {
    colorClasses = 'bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-500/20';
    dotColor = 'bg-rose-500';
    Icon = XCircle;
    defaultLabel = normStatus === 'error' ? 'Error' : 'Offline';
  } else if (normStatus === 'disconnected') {
    colorClasses = 'bg-zinc-100 text-zinc-600 dark:bg-zinc-800/80 dark:text-zinc-400 border-zinc-200 dark:border-zinc-700';
    dotColor = 'bg-zinc-400';
    Icon = Radio;
    defaultLabel = 'Disconnected';
  }

  const textLabel = label || defaultLabel;
  const padding = size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs';

  return (
    <span
      role="status"
      aria-label={`Status: ${textLabel}`}
      className={`inline-flex items-center gap-1.5 rounded-full font-medium border capitalize ${colorClasses} ${padding}`}
    >
      {showDot && (
        <span className="relative flex h-2 w-2">
          {pulse && (
            <span
              className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-75 ${dotColor}`}
            />
          )}
          <span className={`relative inline-flex h-2 w-2 rounded-full ${dotColor}`} />
        </span>
      )}
      <span>{textLabel}</span>
    </span>
  );
}
