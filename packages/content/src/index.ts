import catalogData from "./catalog.json";

export type ContentKind =
  | "pretest_question"
  | "posttest_question"
  | "core_activity"
  | "reinforcement_activity";

export type InteractionType =
  | "choose_one"
  | "listen_choose_one"
  | "choose_image"
  | "listen_choose_image"
  | "choose_many"
  | "listen_choose_many"
  | "sequence"
  | "memory_sequence"
  | "path_sequence"
  | "build_word"
  | "read_aloud"
  | "timed_read_aloud";

export interface MediaRef {
  asset_id: string;
  asset_type: "audio" | "image";
  usage: string;
  semantic_text: string;
}

export interface MediaGap {
  asset_type: "audio" | "image";
  usage: string;
  semantic_text: string;
  status: "declared_missing";
  reason: string;
  impact: string;
}

export interface ContentRound {
  round_id: string;
  order_index: number;
  source_text: string;
  media: MediaRef[];
  media_gaps: MediaGap[];
}

export interface ContentItemDef {
  canonical_id: string;
  stable_key: string;
  kind: ContentKind;
  level_id: 1 | 2 | 3;
  order_index: number;
  title: string;
  skill_id: string;
  skill_name: string;
  source_skill_name: string;
  interaction_type: InteractionType;
  source_method: string;
  criterion: string | null;
  note: string | null;
  item_assets: MediaRef[];
  rounds: ContentRound[];
  checksum: string;
}

export interface SkillDef {
  skill_id: string;
  skill_code: string;
  level_id: 1 | 2 | 3;
  name: string;
}

export interface ContentCatalog {
  schema_version: 1;
  catalog_version: string;
  language: "ar";
  direction: "rtl";
  skills: SkillDef[];
  items: ContentItemDef[];
  media_gaps: Array<MediaGap & { item_id: string; round_id: string }>;
}

export const catalog = catalogData as ContentCatalog;
export const contentItems = catalog.items;
export const skills = catalog.skills;
