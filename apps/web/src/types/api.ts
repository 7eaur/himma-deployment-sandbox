// ────────────────────────────────────────────────────────────────────────────
// Himma API Type Definitions — aligned with backend schemas and catalog v2.0
// ────────────────────────────────────────────────────────────────────────────

/** A single answer option for MCQ items */
export interface ContentOption {
  id: number;
  text: string;
  order_index: number;
  // is_correct is intentionally NOT exposed to the client
}

/** A single step within a content item (one question/round) */
export interface ContentStep {
  id: number;
  order_index: number;
  prompt_text: string;
  expected_reading_text: string | null;
  options: ContentOption[];
}

/** A content item (pretest question, posttest question, or activity) */
export interface ContentItem {
  id: number;
  stable_key: string;
  kind: "pretest_question" | "posttest_question" | "core_activity" | "reinforcement_activity";
  level_id: number;
  interaction_type: "multiple_choice" | "read_aloud" | "fill_in_blank";
  order_index: number;
  steps: ContentStep[];
}

/** Assessment session exposed by the B02 student assessment API. */
export interface AssessmentSession {
  id: number;
  session_type: "pretest" | "posttest";
  status: "in_progress" | "completed";
  started_at: string;
  completed_at: string | null;
  elapsed_seconds: number;
}

/** Audio submission awaiting researcher review */
export interface AudioSubmission {
  id: number;
  response_id: number;
  storage_key: string;
  file_size: number;
  mime_type: string;
  duration_seconds: number | null;
  status: "uploaded" | "graded" | "rerecord_required" | "pending_review";
  submitted_at: string;
}

/** Researcher user profile */
export interface ResearcherProfile {
  id: number;
  username: string;
  full_name: string;
  role: "researcher";
}

/** Student profile returned from /profile */
export interface StudentProfile {
  id: number;
  full_name: string;
  access_code: string;
  grade_level: 3;
  current_level: number;
  status: "active" | "inactive";
  posttest_enabled: boolean;
  next_action: "resume" | "pretest" | "learning" | "posttest" | "completed";
  active_session: AssessmentSession | null;
}

/** Student as returned in researcher list */
export interface StudentListItem {
  id: number;
  full_name: string;
  access_code: string;
  grade_level: 3;
  current_level: number;
  status: "active" | "inactive";
  posttest_enabled: boolean;
  posttest_eligible: boolean;
  created_at: string;
}
