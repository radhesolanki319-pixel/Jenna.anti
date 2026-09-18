'use client';

import React from 'react';
import type { LucideIcon } from 'lucide-react';
import { StatusBadge, type BadgeStatusType } from './StatusBadge';

interface MetricCardProps {
  title: string;
  value?: string | number | React.ReactNode;
  subtitle?: string;
  icon: LucideIcon;
  iconColorClass?: string;
  status?: BadgeStatusType | string;
  statusLabel?: string;
  loading?: boolean;
}

export function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  iconColorClass = 'text-primary-600 dark:text-primary-400 bg-primary-500/10',
  status,
  statusLabel,
  loading = false,
}: MetricCardProps) {
  return (
    <div className="rounded-xl border border-border bg-card p-5 shadow-sm transition-all hover:border-primary-500/40">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className={`rounded-xl p-2.5 ${iconColorClass}`}>
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              {title}
            </h3>
            {loading ? (
              <div className="mt-1.5 h-6 w-24 animate-pulse rounded bg-zinc-200 dark:bg-zinc-800" />
            ) : (
              <div className="mt-1 text-lg font-bold tracking-tight text-foreground">
                {value}
              </div>
            )}
          </div>
        </div>

        {status && !loading && (
          <StatusBadge status={status} label={statusLabel} size="sm" />
        )}
      </div>

      {subtitle && (
        <p className="mt-3 text-xs text-zinc-500 dark:text-zinc-400 border-t border-border/60 pt-2.5">
          {subtitle}
        </p>
      )}
    </div>
  );
}
