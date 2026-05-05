"use client";

import { useCallback, useEffect, useRef, useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import {
  BLOCKS,
  BLOCK_DETAIL,
  UPPER_EX,
  LOWER_EX,
  FLARE,
  NUTRITION,
  WEEK_TARGETS,
} from "@/lib/plan-data";
import {
  type Profile,
  type SessionLog,
  type CoachMessage,
  type Adaptation,
  type BlockId,
} from "@/lib/types";
import {
  saveLog as saveLogAction,
  setCurrentWeek as setCurrentWeekAction,
  updateWeight as updateWeightAction,
  clearChat as clearChatAction,
  signOut as signOutAction,
} from "./actions";

type Tab = "plan" | "progress" | "flare" | "nutrition" | "coach";

const QUICK_QUESTIONS = [
  "What should I do this week?",
  "My knee is hurting today",
  "Suggest a recipe",
  "How am I progressing?",
  "Should I push harder?",
  "I missed sessions — help",
];

const RECIPE_CHIPS = [
  "High-protein breakfast",
  "Post-workout meal",
  "Anti-inflammatory dinner",
  "Pre-workout snack",
  "PCOS-friendly lunch",
];

interface Props {
  userEmail: string;
  profile: Profile;
  logs: SessionLog[];
  messages: CoachMessage[];
  adaptations: Adaptation[];
}

export default function AppShell({ profile, logs, messages, adaptations, userEmail }: Props) {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("plan");
  const [stack, setStack] = useState<string[]>(["plan"]);
  const [subView, setSubView] = useState<string | null>(null);
  const [logInitialBlock, setLogInitialBlock] = useState<string>("");
  const [, startTransition] = useTransition();

  // Optimistic week — updates instantly on click, then syncs with server
  const [optimisticWeek, setOptimisticWeek] = useState(profile.current_week);
  useEffect(() => {
    setOptimisticWeek(profile.current_week);
  }, [profile.current_week]);
  const displayProfile = { ...profile, current_week: optimisticWeek };

  // Local chat state — synced with server messages on initial load
  const [chat, setChat] = useState<Array<{ role: "user" | "assistant"; content: string }>>(
    messages.map((m) => ({ role: m.role, content: m.content }))
  );
  const [chatPrefill, setChatPrefill] = useState("");
  const [thinking, setThinking] = useState(false);

  function go(t: Tab) {
    setTab(t);
    setSubView(null);
    setStack([t]);
  }
  function push(sub: string) {
    setStack((s) => [...s, sub]);
    setSubView(sub);
  }
  function back() {
    setStack((s) => {
      if (s.length <= 1) return s;
      const next = s.slice(0, -1);
      setSubView(next.length === 1 ? null : next[next.length - 1]);
      return next;
    });
  }

  const setWeek = useCallback((w: number) => {
    setOptimisticWeek(w);
    startTransition(() => {
      setCurrentWeekAction(w);
    });
  }, []);

  const openLog = useCallback((blockId: string = "") => {
    setLogInitialBlock(blockId);
    setStack((s) => [...s, "log"]);
    setSubView("log");
  }, []);

  const navClass = (t: Tab) => `nav-btn${tab === t ? ` active-${t}` : ""}`;

  return (
    <div className="app">
      <div className="header">
        <div className="header-row">
          <div className="logo">Move &amp; Thrive</div>
          <div className="week-pill">Week {displayProfile.current_week}</div>
        </div>
        <nav className="nav">
          <button className={navClass("plan")} onClick={() => go("plan")}>Plan</button>
          <button className={navClass("progress")} onClick={() => go("progress")}>Progress</button>
          <button className={navClass("flare")} onClick={() => go("flare")}>Flares</button>
          <button className={navClass("nutrition")} onClick={() => go("nutrition")}>Food</button>
          <button className={navClass("coach")} onClick={() => go("coach")}>Coach 💬</button>
        </nav>
      </div>

      {subView && (
        <div className="back-bar" onClick={back}>
          <span>←</span> <span>Back</span>
        </div>
      )}

      <div className="content">
        {!subView && tab === "plan" && (
          <PlanTab
            profile={displayProfile}
            logs={logs}
            adaptations={adaptations}
            onSetWeek={setWeek}
            onPushBlock={(id) => push(`block:${id}`)}
            onOpenLog={() => openLog("")}
            onGoCoach={() => go("coach")}
          />
        )}
        {!subView && tab === "progress" && (
          <ProgressTab
            profile={displayProfile}
            logs={logs}
            onAskCoach={(q) => {
              setChatPrefill(q);
              go("coach");
            }}
          />
        )}
        {!subView && tab === "flare" && (
          <FlareTab
            onAskCoach={(q) => {
              setChatPrefill(q);
              go("coach");
            }}
          />
        )}
        {!subView && tab === "nutrition" && (
          <NutritionTab
            onAskCoach={(q) => {
              setChatPrefill(q);
              go("coach");
            }}
          />
        )}
        {!subView && tab === "coach" && (
          <CoachTab
            chat={chat}
            setChat={setChat}
            thinking={thinking}
            setThinking={setThinking}
            prefill={chatPrefill}
            clearPrefill={() => setChatPrefill("")}
            onSignOut={async () => {
              await signOutAction();
              router.push("/login");
            }}
            userEmail={userEmail}
          />
        )}

        {subView === "log" && (
          <LogTab profile={displayProfile} logs={logs} initialBlock={logInitialBlock} />
        )}

        {subView?.startsWith("block:") && (
          <BlockDetail
            blockId={subView.split(":")[1] as BlockId}
            profile={displayProfile}
            onLog={(id) => openLog(id)}
            onAskCoach={(q) => {
              setChatPrefill(q);
              go("coach");
            }}
          />
        )}
      </div>
    </div>
  );
}

/* -------------------- Plan Tab -------------------- */

function PlanTab({
  profile,
  logs,
  adaptations,
  onSetWeek,
  onPushBlock,
  onOpenLog,
  onGoCoach,
}: {
  profile: Profile;
  logs: SessionLog[];
  adaptations: Adaptation[];
  onSetWeek: (w: number) => void;
  onPushBlock: (id: BlockId) => void;
  onOpenLog: () => void;
  onGoCoach: () => void;
}) {
  const week = profile.current_week;
  const wt = WEEK_TARGETS[week - 1];
  const ws = logs.filter((l) => l.week === week).length;
  const targetCount = parseInt(wt.s, 10);
  const pct = Math.min(100, (ws / targetCount) * 100);
  const lastAdapt = adaptations[0];

  return (
    <>
      <div className="wtabs">
        {[1, 2, 3, 4].map((w) => (
          <div
            key={w}
            className={`wtab${week === w ? " active" : ""}`}
            onClick={() => onSetWeek(w)}
          >
            W{w}
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-label">Week {week} target</div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 3 }}>
          <div style={{ fontSize: 24, fontFamily: "'DM Serif Display', serif" }}>{wt.s}</div>
          <div style={{ fontSize: 11, color: "var(--muted)", textAlign: "right", maxWidth: "55%" }}>{wt.p}</div>
        </div>
        <div className="pb-wrap"><div className="pb" style={{ width: `${pct}%` }} /></div>
        <div style={{ fontSize: 10, color: "var(--muted)", marginTop: 4 }}>
          {ws} session{ws !== 1 ? "s" : ""} logged this week
        </div>
      </div>

      {lastAdapt && (
        <div className="alert alert-pink" style={{ cursor: "pointer" }} onClick={onGoCoach}>
          💬 Coach: &ldquo;{lastAdapt.text}&rdquo;
        </div>
      )}

      <div className="card-label" style={{ marginBottom: 7 }}>Building Blocks — tap to explore</div>
      <div className="block-grid">
        {BLOCKS.map((b) => (
          <div key={b.id} className="block-card" onClick={() => onPushBlock(b.id)}>
            {b.tag && <span className={`block-tag tag-${b.tag}`}>{b.tagLabel}</span>}
            <div className="block-letter" style={{ color: b.color }}>{b.id}</div>
            <div className="block-name">{b.name}</div>
            <div className="block-desc">{b.desc}</div>
          </div>
        ))}
      </div>

      <button className="btn btn-primary" style={{ marginTop: 14 }} onClick={onOpenLog}>
        ✓ Log a session
      </button>

      <div style={{ marginTop: 14 }}>
        <div className="alert alert-warn">⚠️ Spin: stop if lateral knee pain doesn&apos;t ease in 2 min. Max 1x/week.</div>
        <div className="alert alert-info">💙 Always warm up. Non-negotiable with your back + knee.</div>
        <div className="alert alert-pink">🌸 PCOS: max 1 spin/week. Pair with rest or yoga after.</div>
      </div>
    </>
  );
}

/* -------------------- Block Detail -------------------- */

function BlockDetail({
  blockId,
  profile,
  onLog,
  onAskCoach,
}: {
  blockId: BlockId;
  profile: Profile;
  onLog: (id: BlockId) => void;
  onAskCoach: (q: string) => void;
}) {
  if (blockId === "D" || blockId === "E") {
    return <GymDetail type={blockId === "D" ? "upper" : "lower"} profile={profile} onLog={onLog} onAskCoach={onAskCoach} />;
  }
  const b = BLOCKS.find((x) => x.id === blockId)!;
  const d = BLOCK_DETAIL[blockId];
  if (!d) return null;
  return (
    <>
      <div className="card">
        <div className="block-letter" style={{ color: b.color, fontSize: 38 }}>{b.id}</div>
        <div className="card-title" style={{ marginTop: 5 }}>{d.title}</div>
        <p style={{ fontSize: 13, lineHeight: 1.65, color: "var(--muted)", whiteSpace: "pre-wrap" }}>{d.body}</p>
      </div>
      <button className="btn btn-primary" style={{ marginTop: 4 }} onClick={() => onLog(blockId)}>
        Log this session →
      </button>
      <button
        className="btn btn-secondary"
        style={{ marginTop: 8 }}
        onClick={() => onAskCoach(`Tell me more about block ${blockId} — ${b.name}`)}
      >
        Ask coach about this →
      </button>
    </>
  );
}

function GymDetail({
  type,
  profile,
  onLog,
  onAskCoach,
}: {
  type: "upper" | "lower";
  profile: Profile;
  onLog: (id: BlockId) => void;
  onAskCoach: (q: string) => void;
}) {
  const exs = type === "upper" ? UPPER_EX : LOWER_EX;
  const title = type === "upper" ? "D — Upper Body" : "E — Lower Body";
  const wu = type === "upper" ? "Cat-cow + shoulder rolls (2 min)" : "Pelvic tilts + unloaded glute bridges (2 min)";
  const cd = type === "upper" ? "Chest stretch + neck rolls (2 min)" : "Figure-4 stretch + child's pose (2 min)";
  const warn =
    type === "upper"
      ? "⚠️ Neck tightens → reduce weight first. Pain → stop."
      : "⚠️ Outer knee pain → stop. Back pain during RDL → stop immediately.";

  const initialWeights = (profile.weights[type] ?? {}) as Record<string, string>;
  const [local, setLocal] = useState<Record<string, string>>(initialWeights);

  function update(name: string, value: string) {
    setLocal((prev) => ({ ...prev, [name]: value }));
    updateWeightAction(type, name, value);
  }

  return (
    <>
      <div className="card">
        <div className="card-title">{title}</div>
        <div className="alert alert-info" style={{ marginBottom: 10 }}>🔥 Warm-up: {wu}</div>
        <table className="ex-table">
          <thead>
            <tr><th>Exercise</th><th>Sets</th><th>Weight</th></tr>
          </thead>
          <tbody>
            {exs.map((ex) => (
              <tr key={ex.name}>
                <td>
                  <div className="ex-name">{ex.name}</div>
                  <div className="ex-note">{ex.note}</div>
                </td>
                <td style={{ whiteSpace: "nowrap", paddingRight: 6 }}>{ex.sets}</td>
                <td>
                  <input
                    className="w-input"
                    type="text"
                    value={local[ex.name] ?? ""}
                    onChange={(e) => update(ex.name, e.target.value)}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="alert alert-warn" style={{ marginTop: 10 }}>{warn}</div>
        <div className="alert alert-info" style={{ marginTop: 6 }}>❄️ Cool-down: {cd}</div>
      </div>
      <button className="btn btn-primary" style={{ marginTop: 4 }} onClick={() => onLog(type === "upper" ? "D" : "E")}>
        Log this session →
      </button>
      <button
        className="btn btn-secondary"
        style={{ marginTop: 8 }}
        onClick={() => onAskCoach(`Give me tips for the ${title} session today`)}
      >
        Ask coach for tips →
      </button>
    </>
  );
}

/* -------------------- Log Tab -------------------- */

function LogTab({
  profile,
  logs,
  initialBlock = "",
}: {
  profile: Profile;
  logs: SessionLog[];
  initialBlock?: string;
}) {
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [duration, setDuration] = useState("45 min");
  const [mood, setMood] = useState("");
  const [pain, setPain] = useState("");
  const [notes, setNotes] = useState("");
  const [block, setBlock] = useState(initialBlock);
  const [saving, setSaving] = useState(false);

  async function submit() {
    if (!block) {
      alert("Please select a block");
      return;
    }
    setSaving(true);
    await saveLogAction({ blockId: block, date, duration, mood, pain, notes, week: profile.current_week });
    setMood("");
    setPain("");
    setNotes("");
    setBlock("");
    setSaving(false);
  }

  const recent = logs.slice(0, 10);

  return (
    <>
      <div className="card">
        <div className="card-title">Log a Session</div>

        <div className="form-group">
          <label className="form-label">Block</label>
          <select id="bSel" value={block} onChange={(e) => setBlock(e.target.value)}>
            <option value="">Select block...</option>
            {BLOCKS.map((b) => (
              <option key={b.id} value={b.id}>{b.id} — {b.name}</option>
            ))}
          </select>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label className="form-label">Date</label>
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Duration</label>
            <select value={duration} onChange={(e) => setDuration(e.target.value)}>
              {["30 min", "45 min", "60 min", "75 min", "90 min"].map((d) => (
                <option key={d}>{d}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">How did it feel?</label>
          <div className="mood-row">
            {([["😴", "Low"], ["😐", "Ok"], ["😊", "Good"], ["🔥", "Great"]] as const).map(([e, l]) => (
              <div key={l} className={`mood-btn${mood === l ? " sel" : ""}`} onClick={() => setMood(l)}>
                {e}<span className="mood-label">{l}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Pain today?</label>
          <div className="pain-row">
            <div className={`pain-btn${pain === "none" ? " p-none" : ""}`} onClick={() => setPain("none")}>✅ None</div>
            <div className={`pain-btn${pain === "back" ? " p-back" : ""}`} onClick={() => setPain("back")}>🔶 Back</div>
            <div className={`pain-btn${pain === "knee" ? " p-knee" : ""}`} onClick={() => setPain("knee")}>🔴 Knee</div>
            <div className={`pain-btn${pain === "both" ? " p-both" : ""}`} onClick={() => setPain("both")}>⚠️ Both</div>
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Notes / weights used</label>
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="How did it go? Any weights to update?" />
        </div>

        <button className="btn btn-primary" onClick={submit} disabled={saving}>
          {saving ? "Saving…" : "Save Session ✓"}
        </button>
      </div>

      {recent.length > 0 && (
        <>
          <div className="card-label" style={{ marginBottom: 7 }}>Recent Sessions</div>
          {recent.map((l) => (
            <div key={l.id} className={`log-entry${l.pain && l.pain !== "none" ? " flare" : ""}`}>
              <div className="log-date">{l.date} · {l.duration}</div>
              <div className="log-block">
                {l.block_name}
                {l.mood ? ` · ${l.mood}` : ""}
                {l.pain && l.pain !== "none" ? ` · ⚠️ ${l.pain}` : ""}
              </div>
              {l.notes && <div className="log-detail">{l.notes}</div>}
            </div>
          ))}
        </>
      )}
    </>
  );
}

/* -------------------- Progress Tab -------------------- */

function ProgressTab({
  profile,
  logs,
  onAskCoach,
}: {
  profile: Profile;
  logs: SessionLog[];
  onAskCoach: (q: string) => void;
}) {
  const total = logs.length;
  const flares = logs.filter((l) => l.pain && l.pain !== "none").length;
  const good = logs.filter((l) => l.mood === "Good" || l.mood === "Great").length;
  const wd = [1, 2, 3, 4].map((w) => ({
    w,
    count: logs.filter((l) => l.week === w).length,
    blocks: Array.from(new Set(logs.filter((l) => l.week === w).map((l) => l.block_id))),
  }));

  return (
    <>
      <div className="card">
        <div className="card-title">Overview</div>
        <div className="stat-grid">
          <div><div className="stat-num" style={{ color: "var(--accent)" }}>{total}</div><div className="stat-lbl">Sessions</div></div>
          <div><div className="stat-num" style={{ color: "var(--accent3)" }}>{flares}</div><div className="stat-lbl">Flare days</div></div>
          <div><div className="stat-num" style={{ color: "var(--accent2)" }}>{good}</div><div className="stat-lbl">Good/great</div></div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">Weekly Breakdown</div>
        {wd.map((w) => (
          <div key={w.w} style={{ marginBottom: 11 }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 3 }}>
              <span>Week {w.w}{w.w === profile.current_week ? " (current)" : ""}</span>
              <span style={{ color: "var(--muted)" }}>{w.count} session{w.count !== 1 ? "s" : ""} · {w.blocks.join(", ") || "none"}</span>
            </div>
            <div className="pb-wrap">
              <div className="pb" style={{ width: `${Math.min(100, (w.count / 4) * 100)}%`, opacity: w.w !== profile.current_week ? 0.4 : 1 }} />
            </div>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-title">Current Weights</div>
        <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 8 }}>Upper Body (D)</div>
        {UPPER_EX.map((ex) => (
          <div key={ex.name} style={{ display: "flex", justifyContent: "space-between", padding: "5px 0", borderBottom: "1px solid var(--border)", fontSize: 12 }}>
            <span>{ex.name}</span>
            <span style={{ color: "var(--accent)", fontWeight: 600 }}>{profile.weights.upper?.[ex.name] || "—"}</span>
          </div>
        ))}
        <div style={{ fontSize: 11, color: "var(--muted)", margin: "11px 0 6px" }}>Lower Body (E)</div>
        {LOWER_EX.map((ex) => (
          <div key={ex.name} style={{ display: "flex", justifyContent: "space-between", padding: "5px 0", borderBottom: "1px solid var(--border)", fontSize: 12 }}>
            <span>{ex.name}</span>
            <span style={{ color: "var(--accent)", fontWeight: 600 }}>{profile.weights.lower?.[ex.name] || "—"}</span>
          </div>
        ))}
      </div>

      <button className="btn btn-secondary" onClick={() => onAskCoach("Review my progress and suggest adjustments for next week")}>
        Ask coach to review my progress →
      </button>

      {total === 0 && (
        <div className="empty">
          <div className="empty-icon">📊</div>
          <p>Log your first session to see progress!</p>
        </div>
      )}
    </>
  );
}

/* -------------------- Flare Tab -------------------- */

function FlareTab({ onAskCoach }: { onAskCoach: (q: string) => void }) {
  return (
    <>
      <div className="alert alert-green">When in doubt: Block C or F — always available.</div>
      <div className="card">
        <div className="card-title">Swap Table</div>
        <table className="flare-tbl">
          <thead>
            <tr><th>Planned</th><th style={{ color: "var(--warn)" }}>Back 🔶</th><th style={{ color: "var(--danger)" }}>Knee 🔴</th></tr>
          </thead>
          <tbody>
            {FLARE.map((f) => (
              <tr key={f.from}>
                <td style={{ color: "var(--muted)" }}>{f.from}</td>
                <td>{f.back}</td>
                <td>{f.knee}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <div className="card-title">Both flare / exhausted</div>
        {FLARE.map((f) => (
          <div key={f.from} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid var(--border)", fontSize: 12 }}>
            <span style={{ color: "var(--muted)" }}>{f.from}</span>
            <span style={{ color: "var(--accent)" }}>{f.both}</span>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-title">Warning Signs</div>
        <div className="principle">
          <div className="principle-num">🔶</div>
          <div className="principle-text"><strong>Back</strong>Pain (not tightness) during RDL or leg press → stop that exercise.</div>
        </div>
        <div className="principle">
          <div className="principle-num">🔴</div>
          <div className="principle-text"><strong>Knee (lateral)</strong>Outer left knee pain during spin → reduce resistance. Not gone in 2 min → stop.</div>
        </div>
        <div className="principle">
          <div className="principle-num">🌸</div>
          <div className="principle-text"><strong>PCOS cortisol</strong>Wired but exhausted, poor sleep, bloating, craving spikes → rest or Block F.</div>
        </div>
      </div>

      <button className="btn btn-secondary" onClick={() => onAskCoach("My back is flaring up today — what should I do?")}>
        Ask coach about today&apos;s flare →
      </button>
    </>
  );
}

/* -------------------- Nutrition Tab -------------------- */

function NutritionTab({ onAskCoach }: { onAskCoach: (q: string) => void }) {
  const snacks = ["Soy yogurt + berries", "Nuts + banana", "Boiled egg + rice cake", "Edamame + wholegrain cracker"];
  const proteins = ["Tofu", "Tempeh", "Edamame", "Lentils", "Chickpeas", "Eggs", "Soy yogurt", "Quinoa", "Black beans", "Soy milk"];
  return (
    <>
      <div className="card">
        <div className="card-title">6 Principles</div>
        <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 8 }}>Vegetarian · Low lactose · PCOS-friendly</div>
        {NUTRITION.map((p) => (
          <div key={p.n} className="principle">
            <div className="principle-num">{p.n}</div>
            <div className="principle-text"><strong>{p.title}</strong>{p.body}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-title">Protein Sources</div>
        <div className="tag-row">
          {proteins.map((s) => <div key={s} className="food-tag">{s}</div>)}
        </div>
      </div>

      <div className="card">
        <div className="card-title">Pre-Workout Snacks</div>
        {snacks.map((s) => (
          <div key={s} style={{ padding: "7px 0", borderBottom: "1px solid var(--border)", fontSize: 13 }}>🌱 {s}</div>
        ))}
      </div>

      <div className="card">
        <div className="card-title">Want a recipe?</div>
        <div className="chips">
          {RECIPE_CHIPS.map((q) => (
            <div key={q} className="chip" onClick={() => onAskCoach(`${q} — vegetarian, low lactose, PCOS-friendly`)}>{q}</div>
          ))}
        </div>
      </div>
    </>
  );
}

/* -------------------- Coach Tab -------------------- */

function CoachTab({
  chat,
  setChat,
  thinking,
  setThinking,
  prefill,
  clearPrefill,
  onSignOut,
  userEmail,
}: {
  chat: Array<{ role: "user" | "assistant"; content: string }>;
  setChat: React.Dispatch<React.SetStateAction<Array<{ role: "user" | "assistant"; content: string }>>>;
  thinking: boolean;
  setThinking: (v: boolean) => void;
  prefill: string;
  clearPrefill: () => void;
  onSignOut: () => void;
  userEmail: string;
}) {
  const [input, setInput] = useState("");
  const wrapRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (prefill) {
      setInput(prefill);
      clearPrefill();
      inputRef.current?.focus();
    }
  }, [prefill, clearPrefill]);

  useEffect(() => {
    if (wrapRef.current) wrapRef.current.scrollTop = wrapRef.current.scrollHeight;
  }, [chat, thinking]);

  async function send() {
    const msg = input.trim();
    if (!msg || thinking) return;
    setInput("");
    if (inputRef.current) inputRef.current.style.height = "auto";
    const next = [...chat, { role: "user" as const, content: msg }];
    setChat(next);
    setThinking(true);
    try {
      const res = await fetch("/api/coach", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: next.slice(-10) }),
      });
      const data = await res.json();
      const reply = data.reply ?? "Sorry, connection issue. Try again!";
      setChat([...next, { role: "assistant", content: reply }]);
    } catch {
      setChat([...next, { role: "assistant", content: "Connection issue — please try again." }]);
    } finally {
      setThinking(false);
    }
  }

  return (
    <div className="card">
      <div className="card-title">Your Coach 💬</div>
      <div className="chips">
        {QUICK_QUESTIONS.map((q) => (
          <div key={q} className="chip" onClick={() => setInput(q)}>{q}</div>
        ))}
      </div>

      <div className="chat-wrap" ref={wrapRef}>
        {chat.length === 0 && (
          <div className="msg msg-ai">
            👋 Hi! I know your full plan, injuries, goals and progress. Ask me anything — sessions, nutrition, pain, recipes, or adjustments.
          </div>
        )}
        {chat.map((m, i) => (
          <div key={i} className={`msg ${m.role === "user" ? "msg-user" : "msg-ai"}`}>{m.content}</div>
        ))}
        {thinking && <div className="msg msg-ai">⏳ thinking…</div>}
      </div>

      <div className="chat-input-row">
        <textarea
          ref={inputRef}
          className="chat-input"
          placeholder="Ask your coach anything..."
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            e.target.style.height = "auto";
            e.target.style.height = Math.min(e.target.scrollHeight, 100) + "px";
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          rows={1}
        />
        <button className="send-btn" disabled={thinking || !input.trim()} onClick={send}>↑</button>
      </div>

      <button
        className="btn btn-secondary"
        style={{ marginTop: 8, fontSize: 11 }}
        onClick={async () => {
          if (confirm("Clear chat history?")) {
            await clearChatAction();
            setChat([]);
          }
        }}
      >
        Clear chat
      </button>

      <div style={{ marginTop: 14, paddingTop: 10, borderTop: "1px solid var(--border)", fontSize: 11, color: "var(--muted)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span>{userEmail}</span>
        <button
          onClick={onSignOut}
          style={{ background: "none", border: "none", color: "var(--muted)", cursor: "pointer", fontSize: 11, textDecoration: "underline" }}
        >
          Sign out
        </button>
      </div>
    </div>
  );
}
