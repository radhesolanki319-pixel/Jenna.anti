'use client';

import React from 'react';
import { AlertCircle, RefreshCw, X } from 'lucide-react';

interface ErrorBannerProps {
  title?: string;
  message: string;
  requestId?: string | null;
  onRetry?: () => void;
  onDismiss?: () => void;
  variant?: 'danger' | 'warning' | 'info';
}

export function ErrorBanner({
  title = 'System Alert',
  message,
  requestId,
  onRetry,
  onDismiss,
  variant = 'danger',
}: ErrorBannerProps) {
  const isWarning = variant === 'warning';
  const isInfo = variant === 'info';

  const containerStyle = isWarning
    ? 'border-amber-500/20 bg-amber-500/10 text-amber-800 dark:text-amber-200'
    : isInfo
    ? 'border-blue-500/20 bg-blue-500/10 text-blue-800 dark:text-blue-200'
    : 'border-red-500/20 bg-red-500/10 text-red-800 dark:text-red-200';

  const iconColor = isWarning
    ? 'text-amber-600 dark:text-amber-400'
    : isInfo
    ? 'text-blue-600 dark:text-blue-400'
    : 'text-red-600 dark:text-red-400';

  return (
    <div
      role="alert"
      className={`rounded-xl border p-4 shadow-sm transition-all ${containerStyle}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <AlertCircle className={`h-5 w-5 shrink-0 mt-0.5 ${iconColor}`} />
          <div className="space-y-1">
            <h4 className="text-sm font-semibold tracking-tight">{title}</h4>
            <p className="text-xs opacity-90 leading-relaxed">{message}</p>
            {requestId && (
              <p className="text-[11px] opacity-75 font-mono">
                Request ID: {requestId}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {onRetry && (
            <button
              onClick={onRetry}
              className="inline-flex items-center gap-1.5 rounded-lg border border-current px-2.5 py-1 text-xs font-medium hover:bg-black/5 dark:hover:bg-white/5 focus:outline-none focus:ring-2 focus:ring-current transition-colors"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              <span>Retry</span>
            </button>
          )}
          {onDismiss && (
            <button
              onClick={onDismiss}
              aria-label="Dismiss alert"
              className="rounded-lg p-1 opacity-70 hover:opacity-100 hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
