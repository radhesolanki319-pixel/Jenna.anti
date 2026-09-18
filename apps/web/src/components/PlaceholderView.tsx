import Link from 'next/link';
import { ArrowLeft, Clock } from 'lucide-react';
import type { ElementType } from 'react';

interface PlaceholderViewProps {
  title: string;
  description: string;
  phase: string;
  icon: ElementType;
}

export function PlaceholderView({ title, description, phase, icon: Icon }: PlaceholderViewProps) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center p-6">
      <div className="rounded-2xl border border-border bg-card p-8 max-w-lg w-full shadow-sm">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-primary-500/10 text-primary-600 dark:text-primary-400 mb-6">
          <Icon className="h-8 w-8" />
        </div>

        <div className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-600 dark:text-amber-400 border border-amber-500/20 mb-3">
          <Clock className="h-3.5 w-3.5" />
          Planned for {phase}
        </div>

        <h2 className="text-2xl font-bold tracking-tight mb-2">{title}</h2>
        <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-6 leading-relaxed">
          {description}
        </p>

        <div className="rounded-lg bg-zinc-50 dark:bg-zinc-900/50 p-3.5 text-xs text-zinc-500 dark:text-zinc-400 border border-border mb-6">
          <strong>Architectural Scope Note:</strong> This route is a functional navigation extension point. Under the platform roadmap, underlying capabilities activate in their designated phase. No fake AI or simulated responses are used.
        </div>

        <Link
          href="/"
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}
