// shared-types.ts
export type ToolLink = {
  rel: "proof" | "download" | "view" | string;
  href: string;
  label?: string;
};

export type ToolResultEnvelopeV1 = {
  /** Semantic kind for routing/analytics (not for branching UI) */
  kind: string; // e.g. "integritas/stamp_result@v1"

  /** Plain summary for chat transcript */
  summary?: string;

  /** High-level flow state */
  status?: "finalized" | "pending" | "failed" | "unknown";

  /** Useful identifiers */
  ids?: Record<string, string>; // { uid, tx_id, ... }

  /** ISO-8601 UTC timestamps */
  timestamps?: Record<string, string>; // { stamped_at, ... }

  /** Renderable links (client turns into <a>) */
  links?: ToolLink[];

  /** Machine data (kept for copy/export) */
  data?: unknown;

  /** Standard error envelope when failed */
  error?: { code?: string; message: string; details?: unknown };

  /** Optional schema URI for validators */
  $schema?: "https://integritas.dev/schemas/tool-result-v1.json";
};
