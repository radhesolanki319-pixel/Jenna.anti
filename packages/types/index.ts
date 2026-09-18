/**
 * @jenna/types
 * Core TypeScript definitions for the Jenna AI Platform.
 * Phase 1 — Project Foundation
 */

export type ServiceHealthStatus = 'healthy' | 'unhealthy' | 'degraded';

export interface ServiceHealth {
  name: string;
  status: 'healthy' | 'unhealthy';
  detail?: string | null;
}

export interface HealthCheckResponse {
  status: ServiceHealthStatus;
  version: string;
  phase: string;
  timestamp: string;
  services: ServiceHealth[];
}

export type ThemeMode = 'light' | 'dark' | 'system';

export type UserRole = 'admin' | 'user' | 'readonly';

export interface User {
  id: string;
  email: string;
  role: UserRole;
  created_at: string;
}

export interface Session {
  id: string;
  created_at: string;
  expires_at: string;
}

export interface CurrentUserResponse {
  user: User;
  session: Session | null;
  permissions: string[];
}

export interface AuthResponse {
  status: string;
  message: string;
  user: User;
}

export type DomainEventType =
  | 'ai_request'
  | 'ai_response'
  | 'agent_started'
  | 'agent_completed'
  | 'tool_requested'
  | 'tool_completed'
  | 'memory_created'
  | 'memory_retrieved'
  | 'device_connected'
  | 'device_event'
  | 'task_created'
  | 'task_completed'
  | 'voice_event'
  | 'vision_event';

export interface DomainEvent<T = Record<string, any>> {
  event_id: string;
  event_type: DomainEventType;
  timestamp: string;
  user_id?: string | null;
  request_id?: string | null;
  payload: T;
}

export type AuthorizationDecision = 'ALLOWED' | 'DENIED' | 'REQUIRES_CONFIRMATION';

// ==========================================
// Part 2: AI Core Types
// ==========================================

export type TaskType =
  | 'CHAT'
  | 'REASONING'
  | 'CODING'
  | 'ANALYSIS'
  | 'RESEARCH'
  | 'TOOL_REQUEST'
  | 'VISION'
  | 'TOOL_USE';

export type ModelCapability =
  | 'STREAMING'
  | 'VISION'
  | 'TOOL_USE'
  | 'JSON_OUTPUT'
  | 'SYSTEM_INSTRUCTION';

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface AIUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface AIRequest {
  messages: ChatMessage[];
  system_instruction?: string | null;
  model?: string | null;
  provider?: string | null;
  temperature?: number;
  max_tokens?: number;
  task_type?: TaskType;
  metadata?: Record<string, any>;
  request_id?: string;
}

export interface AIResponse {
  text: string;
  provider: string;
  model: string;
  finish_reason: string;
  usage: AIUsage;
  request_id: string;
  latency_ms: number;
  created_at: string;
}

export interface AIModelMetadata {
  model_id: string;
  provider: string;
  display_name: string;
  context_window: number;
  capabilities: string[];
  default_for_tasks: string[];
  is_available: boolean;
}

export interface StreamStartedEvent {
  type: 'stream.started';
  request_id: string;
  provider: string;
  model: string;
}

export interface StreamDeltaEvent {
  type: 'stream.delta';
  request_id: string;
  delta: string;
  index: number;
}

export interface StreamCompletedEvent {
  type: 'stream.completed';
  request_id: string;
  finish_reason: string;
  usage: AIUsage;
  latency_ms: number;
  full_text: string;
}

export interface StreamErrorEvent {
  type: 'stream.error';
  request_id: string;
  error_code: string;
  message: string;
}

export type AIStreamEvent =
  | StreamStartedEvent
  | StreamDeltaEvent
  | StreamCompletedEvent
  | StreamErrorEvent;

// ==========================================
// Part 2 Phase 2: Conversation & Personality Types
// ==========================================

export interface Conversation {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationMessage {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  model?: string | null;
  provider?: string | null;
  metadata: Record<string, any>;
  created_at: string;
}

export interface PersonalitySettings {
  assistant_name: string;
  personality_style: 'warm' | 'professional' | 'playful' | 'concise';
  response_style: 'conversational' | 'structured' | 'direct';
  preferred_language: 'auto' | 'en' | 'hi' | 'hinglish';
  preferred_locale: string;
  verbosity: 'concise' | 'normal' | 'detailed';
  formality: 'casual' | 'neutral' | 'formal';
  humor_level: 'none' | 'subtle' | 'witty';
}

// ==========================================
// Part 3 Phase 1 & 2: Memory & Retrieval Types
// ==========================================

export type MemoryType =
  | 'FACT'
  | 'PREFERENCE'
  | 'PERSONAL_CONTEXT'
  | 'INSTRUCTION'
  | 'CONVERSATION_SUMMARY'
  | 'TASK_CONTEXT'
  | 'TEMPORARY';

export type MemoryStatus =
  | 'CANDIDATE'
  | 'ACTIVE'
  | 'SUPERSEDED'
  | 'ARCHIVED'
  | 'DELETED';

export type MemorySource =
  | 'USER_EXPLICIT'
  | 'USER_CONVERSATION'
  | 'SYSTEM'
  | 'IMPORTED'
  | 'MANUAL';

export type SensitivityClassification =
  | 'SAFE'
  | 'SENSITIVE_CREDENTIAL'
  | 'SENSITIVE_PERSONAL'
  | 'HIGH_RISK';

export type CandidateAction =
  | 'STORE'
  | 'SUPERSEDE'
  | 'CONFIRM'
  | 'IGNORE';

export type FeedbackType =
  | 'USEFUL'
  | 'INCORRECT'
  | 'OUTDATED'
  | 'FORGET'
  | 'EDIT';

export interface MemoryRecord {
  id: string;
  user_id: string;
  conversation_id?: string | null;
  superseded_by_id?: string | null;
  status: MemoryStatus;
  memory_type: MemoryType;
  content: string;
  summary?: string | null;
  importance: number;
  confidence: number;
  source: string;
  metadata: Record<string, any>;
  has_embedding: boolean;
  archived_at?: string | null;
  last_accessed_at: string;
  created_at: string;
  updated_at: string;
}

export interface MemoryListResponse {
  items: MemoryRecord[];
  total: number;
  limit: number;
  offset: number;
}

export interface MemoryCreateInput {
  content: string;
  memory_type?: MemoryType;
  status?: MemoryStatus;
  summary?: string | null;
  importance?: number;
  confidence?: number;
  source?: string;
  conversation_id?: string | null;
  metadata?: Record<string, any>;
}

export interface MemoryUpdateInput {
  content?: string;
  memory_type?: MemoryType;
  status?: MemoryStatus;
  summary?: string | null;
  importance?: number;
  confidence?: number;
  source?: string;
  metadata?: Record<string, any>;
}

export interface MemoryCandidate {
  content: string;
  memory_type: MemoryType;
  importance: number;
  confidence: number;
  reason: string;
  source: string;
  sensitivity: SensitivityClassification;
  suggested_action: CandidateAction;
  supersedes_id?: string | null;
  conversation_id?: string | null;
}

export interface MemoryExtractResponse {
  candidates: MemoryCandidate[];
  count: number;
}

export interface MemoryActionResponse {
  status: string;
  message: string;
  memory?: MemoryRecord | null;
}

export interface MemorySearchResultItem {
  memory: MemoryRecord;
  score: number;
  breakdown: {
    similarity: number;
    importance: number;
    recency: number;
    confidence: number;
    compound_score: number;
  };
}

export interface MemorySearchResponse {
  query: string;
  results: MemorySearchResultItem[];
  count: number;
}

export interface WorkingMemoryResponse {
  items: Record<string, any>;
}

// ==========================================
// Part 4: Specialized Agents & Orchestration
// ==========================================

export type AgentType =
  | 'RESEARCH'
  | 'CODING'
  | 'ANALYSIS'
  | 'WRITING'
  | 'GENERAL_TASK';

export type AgentTaskStatus =
  | 'CREATED'
  | 'QUEUED'
  | 'RUNNING'
  | 'WAITING'
  | 'SUCCEEDED'
  | 'FAILED'
  | 'CANCELLED';

export type TaskPriority =
  | 'LOW'
  | 'NORMAL'
  | 'HIGH'
  | 'CRITICAL';

export interface AgentBudget {
  max_steps: number;
  max_tokens: number;
  timeout_seconds: number;
}

export interface AgentStepTrace {
  id: string;
  task_id: string;
  step_index: number;
  agent_type: string;
  action: string;
  status: string;
  duration_ms: number;
  output_summary: string;
  created_at: string;
}

export interface AgentTask {
  id: string;
  user_id: string;
  parent_task_id?: string | null;
  agent_type: AgentType;
  title: string;
  description: string;
  status: AgentTaskStatus;
  priority: TaskPriority;
  budget: AgentBudget;
  steps_executed: number;
  tokens_used: number;
  context_handoff: Record<string, any>;
  result_summary?: string | null;
  error?: string | null;
  requires_confirmation: boolean;
  confirmation_reason?: string | null;
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
  subtask_count?: number;
}

export interface AgentTaskDetail extends AgentTask {
  traces: AgentStepTrace[];
  subtasks: AgentTask[];
}

export interface AgentTaskCreateInput {
  title: string;
  description?: string;
  agent_type?: AgentType;
  priority?: TaskPriority;
  parent_task_id?: string | null;
  budget?: Partial<AgentBudget>;
  context_handoff?: Record<string, any>;
  auto_decompose?: boolean;
}

export interface AgentDecompositionSubtask {
  title: string;
  description: string;
  agent_type: AgentType;
  order: number;
}

export interface AgentDecompositionPlan {
  original_task: string;
  strategy: string;
  subtasks: AgentDecompositionSubtask[];
}

export interface AgentRegistryItem {
  name: string;
  agent_type: AgentType;
  description: string;
  capabilities: string[];
  default_budget: AgentBudget;
}

// ==========================================
// Part 5: Tools, MCP & Web Research
// ==========================================

export type ToolCategory =
  | 'GENERAL'
  | 'CALCULATOR'
  | 'FILESYSTEM'
  | 'WEB'
  | 'SYSTEM'
  | 'MCP';

export interface ToolParameter {
  name: string;
  type: string;
  description: string;
  required: boolean;
  default?: any;
  enum_values?: string[];
}

export interface ToolDefinition {
  name: string;
  description: string;
  category: ToolCategory;
  parameters: ToolParameter[];
  requires_permission?: string | null;
  is_sensitive: boolean;
  timeout_seconds: number;
  output_max_chars: number;
}

export interface ToolExecutionResult {
  tool_name: string;
  success: boolean;
  data?: any;
  error?: string | null;
  execution_time_ms: number;
  truncated: boolean;
  timestamp: string;
  requires_confirmation: boolean;
  confirmation_reason?: string | null;
}

export interface WebSearchResult {
  title: string;
  url: string;
  snippet: string;
  domain: string;
  published_date?: string | null;
  score?: number;
}

export interface Citation {
  index: number;
  title: string;
  url: string;
  snippet: string;
  source_verified: boolean;
}

export interface ResearchResponse {
  query: string;
  synthesis: string;
  sources_collected: number;
  sources_read: number;
  citations: Citation[];
  execution_time_ms: number;
  timestamp: string;
}

export interface MCPServerInfo {
  name: string;
  connected: boolean;
  server_info: Record<string, any>;
  tools_count: number;
  tools: string[];
}

/**
 * Phase 6 — Voice & Vision Interfaces
 */

export interface VoiceProfile {
  voice_id: string;
  name: string;
  language: string;
  gender: string;
  style: string;
  pitch: number;
  speed: number;
}

export interface AudioTranscription {
  text: string;
  language: string;
  confidence: number;
  duration_seconds: number;
  timestamp: string;
}

export interface VoiceSettings {
  preferred_voice_id: string;
  preferred_language: string;
  auto_playback: boolean;
  speech_rate: number;
  input_mode: string;
  interruption_enabled: boolean;
  store_raw_audio: boolean;
}

export type VoiceTurnState = 'IDLE' | 'LISTENING' | 'PROCESSING' | 'SPEAKING' | 'INTERRUPTED';

export interface TurnDetectionResult {
  is_speech: boolean;
  speech_probability: number;
  silence_duration_ms: number;
  is_turn_complete: boolean;
  should_interrupt: boolean;
}

export interface InterruptionRequest {
  conversation_id?: string | null;
  reason?: string;
}

export interface InterruptionResponse {
  success: boolean;
  interrupted_at: string;
  message: string;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
  label?: string | null;
  confidence: number;
}

export interface VisionAnalysisResult {
  description: string;
  detected_elements: BoundingBox[];
  extracted_text: string[];
  confidence: number;
  is_untrusted_content: boolean;
  sanitized_prompt_context?: string | null;
  timestamp: string;
}

export interface CameraContext {
  is_active: boolean;
  resolution: string;
  framerate: number;
  device_id?: string | null;
  permission_granted: boolean;
}

export interface VisionPrivacySettings {
  allow_camera_capture: boolean;
  retention_hours: number;
  mask_pii_in_ocr: boolean;
  never_silent_activate: boolean;
}

/**
 * Phase 7 — Computer Control Interfaces
 */

export type ComputerScope =
  | 'SCREEN_OBSERVE'
  | 'MOUSE_CLICK'
  | 'KEYBOARD_TYPE'
  | 'APP_NAVIGATE'
  | 'BROWSER_AUTOMATE'
  | 'TERMINAL_EXEC';

export type ComputerActionType =
  | 'OBSERVE'
  | 'CLICK'
  | 'TYPE'
  | 'KEY_PRESS'
  | 'NAVIGATE_APP'
  | 'BROWSER_ACTION'
  | 'TERMINAL_RUN'
  | 'EMERGENCY_STOP';

export type ActionRiskLevel = 'SAFE' | 'SENSITIVE' | 'CRITICAL';

export type CommandStatus =
  | 'PENDING_APPROVAL'
  | 'QUEUED'
  | 'EXECUTING'
  | 'VERIFYING'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED'
  | 'EMERGENCY_STOPPED';

export interface PairedComputer {
  device_id: string;
  user_id: string;
  device_name: string;
  os_platform: string;
  is_authorized: boolean;
  approved_scopes: ComputerScope[];
  ip_address?: string | null;
  paired_at: string;
  last_seen: string;
}

export interface ComputerStepProgress {
  step_number: number;
  stage: string;
  message: string;
  is_terminal: boolean;
  timestamp: string;
}

export interface ComputerExecutionResult {
  command_id: string;
  device_id: string;
  success: boolean;
  action_type: ComputerActionType;
  output: Record<string, any>;
  visual_verification_passed: boolean;
  duration_ms: number;
  error?: string | null;
  timestamp: string;
}

export interface PairingResponse {
  device_id: string;
  pairing_code: string;
  expires_at: string;
  status: string;
}

/**
 * Phase 8 — Controlled Self-Improvement & Evaluation Interfaces
 */

export type ProposalStatus =
  | 'DRAFT'
  | 'PROPOSED'
  | 'SANDBOX_TESTING'
  | 'TESTS_PASSED'
  | 'TESTS_FAILED'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'DEPLOYED_CANARY'
  | 'DEPLOYED_PROD'
  | 'REJECTED'
  | 'ROLLED_BACK';

export type ImprovementCategory =
  | 'PROMPT_OPTIMIZATION'
  | 'MEMORY_RELEVANCE'
  | 'TOOL_EFFICIENCY'
  | 'ROUTING_ACCURACY'
  | 'COST_REDUCTION';

export interface ImprovementProposal {
  proposal_id: string;
  title: string;
  category: ImprovementCategory;
  rationale: string;
  proposed_changes: Record<string, any>;
  baseline_version: string;
  target_version: string;
  status: ProposalStatus;
  requires_human_approval: boolean;
  approved_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SandboxEvaluationResult {
  eval_id: string;
  proposal_id: string;
  tests_total: number;
  tests_passed: number;
  tests_failed: number;
  baseline_latency_ms: number;
  candidate_latency_ms: number;
  quality_score: number;
  regression_detected: boolean;
  security_check_passed: boolean;
  summary: string;
  evaluated_at: string;
}

export interface CanaryDeploymentRecord {
  deployment_id: string;
  proposal_id: string;
  traffic_percentage: number;
  error_rate_threshold: number;
  current_error_rate: number;
  is_healthy: boolean;
  deployed_at: string;
}

export interface RollbackRecord {
  rollback_id: string;
  proposal_id: string;
  reason: string;
  previous_version: string;
  rolled_back_at: string;
}

// ==========================================
// Part 9: Dashboard & Control Center
// ==========================================

export interface AuditEventItem {
  id: string;
  user_id?: string | null;
  event_type: string;
  action: string;
  success: boolean;
  request_id?: string | null;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface AuditStats {
  total_events: number;
  successful_events: number;
  failed_events: number;
}

export interface PendingApprovalsResponse {
  tasks: AgentTask[];
  proposals: ImprovementProposal[];
  total_pending: number;
}

export interface ApprovalDecisionRequest {
  item_type: 'task' | 'proposal';
  item_id: string;
  decision: 'approve' | 'reject';
  reason?: string;
}

export interface PermissionPolicyTier {
  tier: string;
  description: string;
  requires_confirmation: boolean;
}

export interface PermissionPoliciesResponse {
  tiers: PermissionPolicyTier[];
  decision_outcomes: string[];
  governance_invariants: string[];
}

export interface UsageSummaryResponse {
  total_requests: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  avg_latency_ms: number;
  estimated_cost_usd: number;
  daily_quota_tokens: number;
  quota_remaining_tokens: number;
  quota_percent_used: number;
}

export interface UsageLogEntry {
  id: string;
  provider: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  latency_ms: number;
  success: boolean;
  created_at: string;
}

// ==========================================
// Part 10: Android Integration
// ==========================================

export type AndroidDeviceStatus = 'ONLINE' | 'OFFLINE' | 'REVOKED' | 'PAIRING';

export interface AndroidDevice {
  device_id: string;
  user_id: string;
  device_name: string;
  model: string;
  android_version: string;
  sdk_version: number;
  status: AndroidDeviceStatus;
  granted_permissions: string[];
  paired_at: string;
  last_heartbeat: string;
}

export interface AndroidNotificationItem {
  notification_id: string;
  package_name: string;
  title: string;
  text: string;
  posted_at: string;
  is_clearable: boolean;
}

export interface AndroidContextPayload {
  device_id: string;
  foreground_app: string;
  screen_width: number;
  screen_height: number;
  battery_level: number;
  is_charging: boolean;
  network_type: string;
  notifications: AndroidNotificationItem[];
  timestamp: string;
}

export type AndroidActionType =
  | 'TAP'
  | 'SWIPE'
  | 'TYPE_TEXT'
  | 'PRESS_KEY'
  | 'APP_LAUNCH'
  | 'NAVIGATE';

export interface AndroidActionRequest {
  action_type: AndroidActionType;
  x?: number;
  y?: number;
  x2?: number;
  y2?: number;
  text?: string;
  nav_target?: 'BACK' | 'HOME' | 'RECENTS' | 'NOTIFICATIONS' | 'QUICK_SETTINGS';
  package_name?: string;
  confirmed?: boolean;
  reason?: string;
}

export interface AndroidActionResult {
  action_id: string;
  action_type: AndroidActionType;
  success: boolean;
  verification_state: string;
  message: string;
  execution_time_ms: number;
  timestamp: string;
}








