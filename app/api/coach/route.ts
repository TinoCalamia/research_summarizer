import { NextResponse, type NextRequest } from "next/server";
import Anthropic from "@anthropic-ai/sdk";
import { getServerSupabase } from "@/lib/supabase/server";
import type { Profile, SessionLog } from "@/lib/types";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const DEFAULT_MODEL = "claude-sonnet-4-6";

function buildSystemPrompt(profile: Profile, logs: SessionLog[], summary: string | null) {
  const wc = [1, 2, 3, 4].map((w) => logs.filter((l) => l.week === w).length);
  const flares = logs.filter((l) => l.pain && l.pain !== "none").length;
  const recent = logs
    .slice(0, 7)
    .map(
      (l) =>
        `${l.date}: ${l.block_name}, feel=${l.mood ?? "?"}, pain=${l.pain ?? "none"}, notes="${l.notes ?? ""}"`
    )
    .join("\n");

  const conditions = profile.conditions?.length
    ? profile.conditions.map((c) => `${c.name}${c.severity ? ` (${c.severity})` : ""}${c.notes ? ` — ${c.notes}` : ""}`).join("; ")
    : "Herniated disk (lower back flares), partial lateral LEFT knee ligament tear (still recovering), PCOS";

  const diet = profile.diet?.type
    ? `${profile.diet.type}${profile.diet.restrictions?.length ? `, restrictions: ${profile.diet.restrictions.join(", ")}` : ""}${profile.diet.notes ? `. ${profile.diet.notes}` : ""}`
    : "Vegetarian, low lactose (soy products instead of dairy)";

  const goals = profile.goals?.length
    ? profile.goals.join(", ")
    : "Build muscle (biceps, back, push-ups, glutes, legs), lose weight, manage stress & mental health, strengthen knee";

  return `You are a warm, knowledgeable personal fitness and nutrition coach. You wear several hats for this user: personal trainer, fitness guide, nutritionist, PCOS specialist, and physiotherapist. You know everything about them:

HEALTH: ${conditions}.
DIET: ${diet}.
GOALS: ${goals}.
CURRENT WEEK: ${profile.current_week} of 4. Sessions per week: [W1:${wc[0]}, W2:${wc[1]}, W3:${wc[2]}, W4:${wc[3]}]. Flare sessions: ${flares}.

BLOCKS: A=Spin (max 1x/wk W3+, knee risk), B=Pilates (back-safe), C=Yoga (weekly, non-negotiable), D=Gym Upper (incline push-ups, lat pulldown, rows, bicep curls, face pulls), E=Gym Lower (glute bridges, leg press, RDL, clamshells, wall sit, step-ups optional), F=Walk (active recovery, PCOS).

CURRENT WEIGHTS: Upper: ${JSON.stringify(profile.weights?.upper ?? {})} | Lower: ${JSON.stringify(profile.weights?.lower ?? {})}

RECENT SESSIONS:
${recent || "None yet"}

${summary ? `EARLIER CONVERSATION SUMMARY:\n${summary}\n` : ""}
PCOS guidance: Max 1 spin/wk. Strength > cardio. Never train fasted. Anti-inflammatory diet. Soy is fine.
Neck guidance: No overhead press. Reduce weight if neck tightens.
Knee guidance: Stop if outer knee pain during spin or leg press.
Back guidance: Reduce range before reducing weight. Stop RDL if back pain.

Be warm, practical, concise for mobile. Short paragraphs. Specific weight suggestions when relevant. Full recipes when asked (matching the user's diet). Suggest specific plan swaps if user reports pain or missed sessions. Use emoji sparingly.`;
}

export async function POST(request: NextRequest) {
  const supabase = await getServerSupabase();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Not authenticated" }, { status: 401 });

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return NextResponse.json(
      { error: "ANTHROPIC_API_KEY is not set on the server." },
      { status: 500 }
    );
  }

  let body: { messages: Array<{ role: "user" | "assistant"; content: string }> };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }
  const incoming = Array.isArray(body.messages) ? body.messages : [];
  const lastUser = [...incoming].reverse().find((m) => m.role === "user");
  if (!lastUser) return NextResponse.json({ error: "No user message" }, { status: 400 });

  const [profileRes, logsRes, summaryRes] = await Promise.all([
    supabase.from("profiles").select("*").eq("id", user.id).single(),
    supabase.from("session_logs").select("*").eq("user_id", user.id).order("date", { ascending: false }).limit(20),
    supabase.from("coach_summaries").select("summary").eq("user_id", user.id).order("created_at", { ascending: false }).limit(1).maybeSingle(),
  ]);
  if (!profileRes.data) {
    return NextResponse.json({ error: "Profile not found" }, { status: 500 });
  }

  const system = buildSystemPrompt(
    profileRes.data as Profile,
    (logsRes.data ?? []) as SessionLog[],
    (summaryRes.data?.summary as string | undefined) ?? null
  );

  // Persist the user's message before calling the LLM so it survives errors.
  await supabase.from("coach_messages").insert({
    user_id: user.id,
    role: "user",
    content: lastUser.content,
  });

  const client = new Anthropic({ apiKey });
  const model = process.env.ANTHROPIC_MODEL || DEFAULT_MODEL;

  let reply = "";
  try {
    const response = await client.messages.create({
      model,
      max_tokens: 1000,
      system,
      messages: incoming.map((m) => ({ role: m.role, content: m.content })),
    });
    const textBlock = response.content.find((b) => b.type === "text");
    reply = textBlock && textBlock.type === "text" ? textBlock.text : "";
  } catch (e) {
    const message = e instanceof Error ? e.message : "Unknown error";
    return NextResponse.json({ error: `LLM call failed: ${message}` }, { status: 502 });
  }

  await supabase.from("coach_messages").insert({
    user_id: user.id,
    role: "assistant",
    content: reply,
  });

  if (/\b(skip|swap|reduce|adjust|switch to)\b/i.test(reply)) {
    const text = reply.split("\n")[0].slice(0, 80);
    await supabase.from("adaptations").insert({ user_id: user.id, text });
  }

  return NextResponse.json({ reply });
}
