export type BlockId = "A" | "B" | "C" | "D" | "E" | "F";

export type Mood = "" | "Low" | "Ok" | "Good" | "Great";
export type Pain = "" | "none" | "back" | "knee" | "both";

export interface Profile {
  id: string;
  display_name: string | null;
  conditions: Array<{ name: string; severity?: string; notes?: string }>;
  diet: { type?: string; restrictions?: string[]; notes?: string };
  goals: string[];
  current_week: number;
  weights: { upper?: Record<string, string>; lower?: Record<string, string> };
  preferences: Record<string, unknown>;
}

export interface SessionLog {
  id: string;
  user_id: string;
  block_id: BlockId | string;
  block_name: string;
  date: string;
  duration: string | null;
  mood: Mood | null;
  pain: Pain | null;
  notes: string | null;
  week: number | null;
  created_at: string;
}

export interface CoachMessage {
  id: string;
  user_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface Adaptation {
  id: string;
  user_id: string;
  text: string;
  created_at: string;
}

// Default weights matching the original HTML's seed values
export const DEFAULT_WEIGHTS = {
  upper: {
    "Incline Push-ups": "BW",
    "Lat Pulldown": "27kg",
    "Seated Cable Row": "25kg",
    "Bicep Curls": "6kg",
    "Face Pulls": "10kg",
  },
  lower: {
    "Glute Bridges": "BW",
    "Leg Press": "30kg",
    "Romanian Deadlift": "10kg",
    Clamshells: "light band",
    "Wall Sit": "BW",
    "Step-ups (opt.)": "BW",
  },
};
