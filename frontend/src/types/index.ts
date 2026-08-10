// Frontend TypeScript types aligned with backend schemas

export interface HealthResponse {
  status: string;
  offline: boolean;
  version: string;
  timestamp: string;
}

export interface SystemStatusResponse {
  status: string;
  offline: boolean;
  version: string;
  environment: string;
  uptime_seconds: number;
  has_c_compiler: boolean;
  has_fortran_compiler: boolean;
  local_ai_enabled: boolean;
  timestamp: string;
}

export interface CompilerInfo {
  name: string;
  language: string;
  status: 'detected' | 'not_found' | 'error';
  path?: string;
  version?: string;
  version_string?: string;
  error?: string;
}

export interface SystemInfoResponse {
  os_name: string;
  os_version: string;
  os_platform: string;
  python_version: string;
  python_executable: string;
  architecture: string;
  cpu_count: number;
  total_memory_gb: number;
  available_memory_gb: number;
  disk_total_gb: number;
  disk_used_gb: number;
  disk_free_gb: number;
  disk_percent_used: number;
  node_version?: string;
  c_compilers: CompilerInfo[];
  fortran_compilers: CompilerInfo[];
  app_version: string;
  offline: boolean;
  local_ai_enabled: boolean;
  local_ai_provider?: string;
  timestamp: string;
}

export interface FunctionAnalysis {
  name: string;
  kind: string;
  parameters: string[];
  return_type?: string;
  loc: number;
  cyclomatic_complexity: number;
  has_loops: boolean;
  has_conditionals: boolean;
  has_io: boolean;
  has_implicit_none?: boolean;
  calls: string[];
}

export interface AnalysisResult {
  session_id: string;
  status: string;
  c_analysis: {
    filename: string;
    parser_used: string;
    total_lines: number;
    total_loc: number;
    functions: FunctionAnalysis[];
    constants: { name: string; value?: string }[];
    includes: string[];
    warnings: string[];
  };
  fortran_analysis: {
    filename: string;
    parser_used: string;
    total_lines: number;
    total_loc: number;
    functions: FunctionAnalysis[];
    constants: { name: string; value?: string }[];
    modules: string[];
    warnings: string[];
  };
  ir_summary: {
    structural_score: number;
    matched_functions: [string, string][];
    c_only_functions: string[];
    fortran_only_functions: string[];
    notes: string[];
  };
  gaps: GapReport[];
  created_at: string;
}

export interface GapReport {
  id: string;
  gap_id: string;
  category: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  source_language: string;
  target_language: string;
  location: string;
  explanation: string;
  evidence: string;
  confidence: number;
  suggested_resolution: string;
  status: string;
}

export interface AnalysisSummary {
  session_id: string;
  status: string;
  c_filename?: string;
  fortran_filename?: string;
  c_functions_found?: number;
  fortran_functions_found?: number;
  gaps_detected?: number;
  high_severity_gaps?: number;
  created_at?: string;
  completed_at?: string;
}
