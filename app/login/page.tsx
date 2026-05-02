"use client";
import { useState } from "react";
import { getBrowserSupabase } from "@/lib/supabase/client";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("sending");
    setError(null);
    const supabase = getBrowserSupabase();
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: `${window.location.origin}/auth/callback` },
    });
    if (error) {
      setStatus("error");
      setError(error.message);
    } else {
      setStatus("sent");
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-card">
        <div className="logo">Move &amp; Thrive</div>
        <div className="tagline">Your personal coach, physio, and nutritionist — in one place.</div>

        {status === "sent" ? (
          <div className="alert alert-green">
            ✉️ Check your inbox for a magic link at <strong>{email}</strong>.
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
              />
            </div>
            <button className="btn btn-primary" disabled={status === "sending"}>
              {status === "sending" ? "Sending magic link…" : "Send magic link"}
            </button>
            {error && <div className="alert alert-warn" style={{ marginTop: 10 }}>{error}</div>}
          </form>
        )}
      </div>
    </div>
  );
}
