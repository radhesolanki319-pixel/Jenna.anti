import { PlaceholderView } from '@/components/PlaceholderView';
import { CheckSquare } from 'lucide-react';

export default function TasksPage() {
  return (
    <PlaceholderView
      title="Tasks"
      description="Background task scheduling, recurring jobs, automation workflows, and execution audit history."
      phase="Phase 7"
      icon={CheckSquare}
    />
  );
}
