import type { UserRole, User, Session, CurrentUserResponse, AuthResponse } from './auth';

export type { UserRole, User, Session, CurrentUserResponse, AuthResponse };

export type HealthStatus = 'healthy' | 'unhealthy' | 'degraded' | 'ok' | 'not_ready';

export interface ServiceDependencyHealth {
  name: string;
  status: string;
  detail?: string | null;
}

export interface ComprehensiveHealthResponse {
  status: string;
  service: string;
  version: string;
  phase: string;
  timestamp: string;
  services: ServiceDependencyHealth[];
}

export interface LivenessResponse {
  status: string;
  service: string;
  timestamp: string;
}

export interface ReadinessResponse {
  status: string;
  ready: boolean;
  service: string;
  dependencies: Record<string, boolean>;
  timestamp: string;
}

export interface SystemInfoResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
  platform: string;
  python_version: string;
  uptime_seconds: number;
  uptime_formatted: string;
  timestamp: string;
  settings: Record<string, any>;
}

export type WebSocketConnectionStatus =
  | 'connecting'
  | 'connected'
  | 'disconnected'
  | 'reconnecting'
  | 'error';

export interface WebSocketMessage {
  type: string;
  timestamp?: string;
  client_id?: string;
  service?: string;
  features?: string[];
  channels?: string[];
  code?: string;
  message?: string;
  [key: string]: any;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: Record<string, any>;
  request_id?: string | null;
  timestamp?: string;
}

export interface ApiErrorResponse {
  error: ApiErrorDetail;
}
