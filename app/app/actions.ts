"use server";

import { revalidatePath } from "next/cache";
import { getServerSupabase } from "@/lib/supabase/server";
import { BLOCKS } from "@/lib/plan-data";
import type { BlockId } from "@/lib/types";

async function userId() {
  const supabase = await getServerSupabase();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) throw new Error("Not authenticated");
  return { supabase, userId: user.id };
}

export async function setCurrentWeek(week: number) {
  const { supabase, userId: uid } = await userId();
  await supabase.from("profiles").update({ current_week: week }).eq("id", uid);
  revalidatePath("/app");
}

export async function updateWeight(group: "upper" | "lower", exercise: string, value: string) {
  const { supabase, userId: uid } = await userId();
  const { data: profile } = await supabase.from("profiles").select("weights").eq("id", uid).single();
  const weights = (profile?.weights ?? {}) as { upper?: Record<string, string>; lower?: Record<string, string> };
  const updated = {
    ...weights,
    [group]: { ...(weights[group] ?? {}), [exercise]: value },
  };
  await supabase.from("profiles").update({ weights: updated }).eq("id", uid);
  revalidatePath("/app");
}

export async function saveLog(input: {
  blockId: BlockId | string;
  date: string;
  duration: string;
  mood: string;
  pain: string;
  notes: string;
  week: number;
}) {
  const { supabase, userId: uid } = await userId();
  const block = BLOCKS.find((b) => b.id === input.blockId);
  await supabase.from("session_logs").insert({
    user_id: uid,
    block_id: input.blockId,
    block_name: block ? `${block.id} — ${block.name}` : input.blockId,
    date: input.date,
    duration: input.duration,
    mood: input.mood || null,
    pain: input.pain || null,
    notes: input.notes || null,
    week: input.week,
  });
  revalidatePath("/app");
}

export async function clearChat() {
  const { supabase, userId: uid } = await userId();
  await supabase.from("coach_messages").delete().eq("user_id", uid);
  revalidatePath("/app");
}

export async function signOut() {
  const supabase = (await getServerSupabase());
  await supabase.auth.signOut();
}
