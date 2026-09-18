export type SectionId =
  | 'overview'
  | 'board'
  | 'attention'
  | 'repos'
  | 'skills'
  | 'plugins'
  | 'mcp'
  | 'hooks'
  | 'codex';

export type ConfigTone = '' | 'on' | 'off' | 'muted';

export interface ConfigRow {
  label: string;
  value: string;
  tone?: ConfigTone;
}

export interface ConfigGroup {
  title: string;
  source: string;
  rows: ConfigRow[];
}

export type ItemKind = 'skill' | 'plugin' | 'mcp' | 'hook' | 'repo' | 'dev_server' | 'warning';

export interface ItemDetails {
  origin?: string;
  source_path?: string;
  openai_yaml_path?: string;
  codex_allow_implicit_invocation?: boolean;
  codex_invocation?: string;
  repo?: string;
  marketplace?: string;
  category?: string;
  global?: boolean;
  transport?: string;
  url?: string;
  plugins?: string[];
  path?: string;
  model?: string;
  reasoning?: string;
  features?: Record<string, unknown>;
  event?: string;
  timeout?: number;
  code?: string;
  servers?: string[];
  server_count?: number;
  ports?: number[];
  skill_count?: number;
  plugin_count?: number;
  mcp_count?: number;
  hook_count?: number;
  dev_count?: number;
  [key: string]: unknown;
}

export interface Item {
  id: string;
  kind: ItemKind;
  name: string;
  title: string;
  scope: string;
  status: string;
  repos: string[];
  source: string;
  details: ItemDetails;
  search_text: string;
  /** Attached only on synthesized attention items. */
  attentionType?: AttentionType;
}

export interface Warning {
  message: string;
  severity?: string;
  code: string;
  source: string;
}

export interface SourceRef {
  path: string;
  absolute_path?: string;
}

export interface Counts {
  items: number;
  skills: number;
  plugins: number;
  mcp: number;
  repos: number;
  hooks: number;
  dev_servers: number;
  warnings: number;
  global: number;
  repo_scoped: number;
  disabled: number;
}

export interface Groups {
  skills: Item[];
  plugins: Item[];
  mcp: Item[];
  repos: Item[];
  hooks: Item[];
  dev_servers: Item[];
}

export type CapabilityStatus = 'stable' | 'new' | 'planned' | 'na';

export interface CapabilityState {
  status: CapabilityStatus;
  note: string;
}

export interface Capability extends CapabilityState {
  key: string;
  name: string;
  desc: string;
  source: string;
  count: number | null;
}

export interface ControlPlaneData {
  schema_version: string;
  generated_at_utc: string;
  repo_root: string;
  capabilities?: Capability[];
  global_config?: ConfigGroup[];
  sources: Record<string, SourceRef>;
  counts: Counts;
  warnings: Warning[];
  items: Item[];
  groups: Groups;
}

export type AttentionType =
  | 'warnings'
  | 'unassigned'
  | 'disabled'
  | 'dormant'
  | 'unscoped';

export type Tone = '' | 'warning' | 'ok' | 'scope-global' | 'scope-local';
