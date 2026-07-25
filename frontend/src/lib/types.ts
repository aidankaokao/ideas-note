export type User = { id: number; username: string; is_admin: boolean; created_at?: string };

export type Note = {
  id: number;
  title: string;
  content: string;
  source: string; // manual / agent-extend / qa-extract
  created_at: string;
  updated_at: string;
  has_embedding?: boolean;
  score?: number;
};

export type NoteLink = {
  id: number;
  other_note_id: number;
  other_title: string;
  reason: string;
  direction: "out" | "in";
};

export type Topic = {
  id: number;
  name: string;
  summary: string;
  notes: { id: number; title: string }[];
};

export type Provider = {
  id: number;
  name: string;
  provider: "openai" | "ollama";
  base_url: string;
  model: string;
  api_key: string; // 後端回遮罩值
  temperature: number;
};

export type ActiveProviders = {
  chat_provider_id: number | null;
  embedding_provider_id: number | null;
};

export type ExtendResult = {
  extensions: { title: string; idea: string }[];
  questions: string[];
  next_steps: string[];
};

export type ConnectResult = {
  summary: string;
  combinations: { note_id: number; note_title: string; score: number; idea: string }[];
  related: { id: number; title: string; score: number }[];
};

export type QAResult = {
  answer: string;
  sparks: { title: string; content: string }[];
  sources: { id: number; title: string; score: number }[];
};

export type MindmapResult = { markdown: string; note_count: number };

// ── 靈感導師 ──

export type MentorAction =
  | { type: "note_created"; note_id: number; title: string }
  | {
      type: "note_update_proposal";
      note_id: number;
      old_title: string;
      new_title: string;
      new_content: string;
      reason: string;
    }
  | { type: "mindmap_saved"; id: number; title: string }
  | { type: "topics_updated"; topics: { name: string; count: number }[] };

export type MentorPayload = { suggestions?: string[]; actions?: MentorAction[] };

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  payload?: MentorPayload | null;
};

export type Briefing = { greeting: string; suggestions: string[] };

export type MentorContext = { used: number; budget: number; percent: number; summary: string };

export type Mindmap = {
  id: number;
  title: string;
  markdown: string;
  topic_id?: number | null;
  query?: string | null;
  created_at: string;
};
