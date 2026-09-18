import { PlaceholderView } from '@/components/PlaceholderView';
import { Settings } from 'lucide-react';

export default function SettingsPage() {
  return (
    <PlaceholderView
      title="Settings"
      description="User preferences, authentication providers, API keys, and platform telemetry configuration."
      phase="Phase 2"
      icon={Settings}
    />
  );
}
