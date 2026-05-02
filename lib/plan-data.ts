import type { BlockId } from "./types";

export interface Block {
  id: BlockId;
  name: string;
  desc: string;
  tag: "" | "knee" | "key" | "pcos";
  tagLabel: string;
  color: string;
}

export const BLOCKS: Block[] = [
  { id: "A", name: "Spin Class", desc: "Cardio + joy", tag: "knee", tagLabel: "⚠️ Knee", color: "#f07ac8" },
  { id: "B", name: "Pilates", desc: "Core + back rehab", tag: "key", tagLabel: "✓ Back", color: "#7ac8f0" },
  { id: "C", name: "Yoga", desc: "Recovery + stress", tag: "key", tagLabel: "Non-neg.", color: "#c8f07a" },
  { id: "D", name: "Gym Upper", desc: "Biceps + push-ups", tag: "", tagLabel: "", color: "#f0c87a" },
  { id: "E", name: "Gym Lower", desc: "Glutes + knee rehab", tag: "", tagLabel: "", color: "#c87af0" },
  { id: "F", name: "Walk", desc: "Active recovery", tag: "pcos", tagLabel: "PCOS ✓", color: "#7af0c8" },
];

export const BLOCK_DETAIL: Partial<Record<BlockId, { title: string; body: string }>> = {
  A: {
    title: "A — Spin Class",
    body: `45–60 min. Max 1x/week from Week 3.

Knee rule: if left lateral knee hurts, reduce resistance. Not gone in 2 min → stop.

PCOS: pair with rest or yoga after. Max 1x/week.`,
  },
  B: {
    title: "B — Pilates",
    body: `45–60 min. 1–2x/week.

Tell your instructor about your herniated disk and knee. Great choice when back is grumpy.`,
  },
  C: {
    title: "C — Yoga",
    body: `45–60 min. 1x/week minimum — non-negotiable.

Avoid deep forward folds (back) and deep lunges (knee). Your recovery and mental health anchor.`,
  },
  F: {
    title: "F — Walk",
    body: `20–40 min. Use on rest or flare days.

Week 1–2: 1x/week. Week 3–4: aim 2x/week.

Steady walking supports cortisol, insulin sensitivity and mood.`,
  },
};

export interface Exercise {
  name: string;
  sets: string;
  note: string;
}

export const UPPER_EX: Exercise[] = [
  { name: "Incline Push-ups", sets: "3x8", note: "Do first while fresh — push-up progression" },
  { name: "Lat Pulldown", sets: "3x8", note: "Controlled, no yanking neck" },
  { name: "Seated Cable Row", sets: "3x8", note: "Squeeze blades, don't hunch" },
  { name: "Bicep Curls", sets: "3x10", note: "Slow on the way down" },
  { name: "Face Pulls", sets: "3x12", note: "Neck protection — never skip" },
];

export const LOWER_EX: Exercise[] = [
  { name: "Glute Bridges", sets: "4x12", note: "Drive through heels, not toes" },
  { name: "Leg Press", sets: "4x10", note: "Feet high, don't lock knees at top" },
  { name: "Romanian Deadlift", sets: "3x10", note: "Hinge at hips, soft knees, back straight" },
  { name: "Clamshells", sets: "3x15", note: "Each side, slow and controlled" },
  { name: "Wall Sit", sets: "2x40s", note: "Stop at pain, not just burn" },
  { name: "Step-ups (opt.)", sets: "3x8", note: "⚡ Skip if knee is grumpy today" },
];

export const FLARE = [
  { from: "D — Upper", back: "✅ Do as normal", knee: "✅ Do as normal", both: "→ Block C" },
  { from: "E — Lower", back: "→ Block B", knee: "Skip leg press + RDL + step-ups", both: "→ Block F" },
  { from: "A — Spin", back: "→ Block B or C", knee: "→ Block B or C", both: "→ Block F" },
  { from: "B — Pilates", back: "✅ Tell instructor", knee: "✅ Tell instructor", both: "→ Block F" },
  { from: "C — Yoga", back: "Avoid fwd folds", knee: "Avoid deep lunges", both: "✅ Always ok" },
];

export const NUTRITION = [
  { n: 1, title: "Protein at every meal", body: "Tofu, tempeh, edamame, lentils, chickpeas, eggs, soy yogurt, quinoa — always present, not an afterthought." },
  { n: 2, title: "Never skip breakfast", body: "PCOS + cortisol are worse on empty. Even something small counts." },
  { n: 3, title: "Reduce refined carbs — don't eliminate", body: "Small swaps to wholegrain. No overhaul needed." },
  { n: 4, title: "Eat before training", body: "Small snack 30–60 min before. Never train fasted — cortisol spike with PCOS." },
  { n: 5, title: "Anti-inflammatory foods", body: "Berries, leafy greens, olive oil, nuts. PCOS is an inflammatory condition." },
  { n: 6, title: "Watch iron + B12", body: "Vegetarian + PCOS = risk of low levels. Get checked if energy tanks." },
];

export const WEEK_TARGETS = [
  { s: "2–3x", p: "C + D or E + walk" },
  { s: "2–3x", p: "C + D or E + walk" },
  { s: "3–4x", p: "C + A + D + E + walk" },
  { s: "3–4x", p: "C + A + D + E + walk" },
];
