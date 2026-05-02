import { redirect } from "next/navigation";
import { getServerSupabase } from "@/lib/supabase/server";
import { DEFAULT_WEIGHTS, type Profile, type SessionLog, type CoachMessage, type Adaptation } from "@/lib/types";
import AppShell from "./AppShell";

export const dynamic = "force-dynamic";

export default async function AppPage() {
  const supabase = await getServerSupabase();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const [profileRes, logsRes, messagesRes, adaptationsRes] = await Promise.all([
    supabase.from("profiles").select("*").eq("id", user.id).single(),
    supabase.from("session_logs").select("*").eq("user_id", user.id).order("date", { ascending: false }).limit(100),
    supabase.from("coach_messages").select("*").eq("user_id", user.id).order("created_at", { ascending: true }).limit(50),
    supabase.from("adaptations").select("*").eq("user_id", user.id).order("created_at", { ascending: false }).limit(3),
  ]);

  // If the post-signup trigger hasn't run yet (or this is an existing user from before the trigger), seed a profile.
  let profile = profileRes.data as Profile | null;
  if (!profile) {
    const seeded = {
      id: user.id,
      weights: DEFAULT_WEIGHTS,
    };
    const { data } = await supabase.from("profiles").upsert(seeded).select("*").single();
    profile = data as Profile;
  } else if (!profile.weights || Object.keys(profile.weights).length === 0) {
    const { data } = await supabase
      .from("profiles")
      .update({ weights: DEFAULT_WEIGHTS })
      .eq("id", user.id)
      .select("*")
      .single();
    profile = data as Profile;
  }

  return (
    <AppShell
      userEmail={user.email ?? ""}
      profile={profile}
      logs={(logsRes.data ?? []) as SessionLog[]}
      messages={(messagesRes.data ?? []) as CoachMessage[]}
      adaptations={(adaptationsRes.data ?? []) as Adaptation[]}
    />
  );
}
