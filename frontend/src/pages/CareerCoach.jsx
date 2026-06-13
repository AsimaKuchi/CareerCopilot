/**
 * CareerCoach.jsx
 *
 * Chat UI for the "Brutal Mentor" career coach.
 *
 * Routes:
 *   /coach          - landing if no session, OR resumes the most recent session
 *   /coach/:id      - resume a specific session
 *
 * The chat:
 *   - Loads (or creates) a session
 *   - Streams the coach's responses token-by-token
 *   - Shows a 'Generate 3 paths from this conversation' CTA once the
 *     backend flags ready_to_synthesize OR the user manually triggers it
 *   - After synthesis succeeds, navigates back to /career-paths which
 *     will render the new analysis automatically
 */
import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { API } from "@/App";
import { apiFetch } from "@/utils/apiFetch";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import Navbar from "@/components/Navbar";
import { Loader2, Send, Sparkles, Trash2, ArrowLeft } from "lucide-react";
import { toast } from "sonner";

export default function CareerCoach() {
  const { id: paramSessionId } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [synthesizing, setSynthesizing] = useState(false);
  // Live-streaming token buffer for the in-flight assistant reply.
  const [streamingText, setStreamingText] = useState("");
  const scrollRef = useRef(null);

  // -------- Lifecycle --------
  useEffect(() => {
    (async () => {
      try {
        if (paramSessionId) {
          const r = await apiFetch(`${API}/coach/sessions/${paramSessionId}`);
          if (!r.ok) throw new Error("Session not found");
          setSession(await r.json());
        } else {
          // No id in URL - start a fresh session
          const r = await apiFetch(`${API}/coach/sessions`, { method: "POST" });
          if (!r.ok) {
            const e = await r.json().catch(() => ({}));
            if (r.status === 402) {
              toast.error(e.detail?.message || "Monthly limit reached");
              navigate("/pricing");
              return;
            }
            throw new Error(e.detail || "Failed to start session");
          }
          const fresh = await r.json();
          setSession(fresh);
          navigate(`/coach/${fresh.session_id}`, { replace: true });
        }
      } catch (e) {
        toast.error(e.message || "Failed to load coach");
        navigate("/career-paths");
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramSessionId]);

  // -------- Autoscroll on new content --------
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [session?.messages, streamingText]);

  // -------- Send a message --------
  const sendMessage = async () => {
    const text = draft.trim();
    if (!text || !session || sending) return;
    setDraft("");
    setSending(true);
    setStreamingText("");

    // Optimistically render the user's message immediately
    const optimistic = {
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };
    setSession((s) => ({ ...s, messages: [...s.messages, optimistic] }));

    try {
      const r = await apiFetch(`${API}/coach/sessions/${session.session_id}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      if (!r.ok) {
        const e = await r.json().catch(() => ({}));
        throw new Error(e.detail || "Coach failed to respond");
      }
      const reader = r.body?.getReader();
      if (!reader) {
        const t = await r.text();
        setStreamingText(t);
      } else {
        const decoder = new TextDecoder();
        let full = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          full += decoder.decode(value, { stream: true });
          setStreamingText(full);
        }
      }
      // Refetch the session to pull the persisted assistant message
      // (including any ready_to_synthesize flip) and clear the streaming buffer.
      const fresh = await apiFetch(`${API}/coach/sessions/${session.session_id}`);
      if (fresh.ok) setSession(await fresh.json());
      setStreamingText("");
    } catch (e) {
      toast.error(e.message || "Failed to send message");
    } finally {
      setSending(false);
    }
  };

  // -------- Synthesize paths --------
  const synthesize = async () => {
    if (!session || synthesizing) return;
    setSynthesizing(true);
    try {
      const r = await apiFetch(
        `${API}/coach/sessions/${session.session_id}/synthesize`,
        { method: "POST" }
      );
      if (!r.ok) {
        const e = await r.json().catch(() => ({}));
        throw new Error(e.detail || "Failed to generate paths");
      }
      toast.success("Paths generated! Loading your tailored analysis...");
      navigate("/career-paths");
    } catch (e) {
      toast.error(e.message || "Synthesis failed");
    } finally {
      setSynthesizing(false);
    }
  };

  // -------- Delete --------
  const deleteSession = async () => {
    if (!session) return;
    if (!window.confirm("Delete this coaching session? This can't be undone.")) return;
    try {
      const r = await apiFetch(`${API}/coach/sessions/${session.session_id}`, {
        method: "DELETE",
      });
      if (!r.ok) throw new Error("Delete failed");
      toast.success("Session deleted");
      navigate("/career-paths");
    } catch (e) {
      toast.error(e.message);
    }
  };

  // -------- Render --------
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
      </div>
    );
  }

  const messages = session?.messages || [];
  const readyToSynthesize = session?.ready_to_synthesize;
  const exchangeCount = messages.filter((m) => m.role === "user").length;
  const canManualSynth = exchangeCount >= 3;

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <Navbar />
      <div className="max-w-3xl mx-auto px-4 pt-6 pb-32">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <button
            data-testid="back-to-paths-btn"
            onClick={() => navigate("/career-paths")}
            className="text-slate-500 hover:text-slate-700 flex items-center gap-2 text-sm"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Career Paths
          </button>
          <button
            data-testid="delete-coach-session-btn"
            onClick={deleteSession}
            className="text-rose-500 hover:text-rose-600 flex items-center gap-2 text-sm"
            title="Delete this conversation"
          >
            <Trash2 className="w-4 h-4" />
            End session
          </button>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          {/* Coach intro banner */}
          <div className="bg-slate-900 text-white px-6 py-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-amber-500 flex items-center justify-center text-slate-900 font-bold text-lg">
                M
              </div>
              <div>
                <div className="font-bold">Your Career Mentor</div>
                <div className="text-xs text-slate-400">
                  Direct & honest. No fluff. {exchangeCount} of ~6-8 messages exchanged.
                </div>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="h-[60vh] overflow-y-auto px-6 py-6 space-y-5" data-testid="coach-messages">
            {messages.map((m, i) => (
              <Bubble key={i} role={m.role} content={m.content} />
            ))}
            {sending && streamingText && (
              <Bubble role="assistant" content={streamingText} streaming />
            )}
            {sending && !streamingText && (
              <div className="text-slate-400 text-sm flex items-center gap-2 pl-12">
                <Loader2 className="w-3 h-3 animate-spin" />
                Coach is thinking...
              </div>
            )}
          </div>

          {/* Synthesize CTA when ready */}
          {(readyToSynthesize || canManualSynth) && (
            <div className="border-t border-amber-200 bg-amber-50 px-6 py-4">
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
                <Sparkles className="w-5 h-5 text-amber-600 flex-shrink-0" />
                <div className="flex-1">
                  <div className="font-semibold text-slate-900">
                    {readyToSynthesize
                      ? "Ready to propose 3 paths"
                      : "Want me to propose paths now?"}
                  </div>
                  <div className="text-sm text-slate-600">
                    {readyToSynthesize
                      ? "I have enough signal. I'll turn this conversation into 3 concrete career paths with salary ranges, skill gaps and next steps."
                      : "We can keep talking, or I can take a first cut based on what you've told me so far."}
                  </div>
                </div>
                <Button
                  data-testid="synthesize-paths-btn"
                  onClick={synthesize}
                  disabled={synthesizing}
                  className="bg-amber-500 hover:bg-amber-600 text-slate-900 font-semibold"
                >
                  {synthesizing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      Generate 3 paths
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}

          {/* Composer */}
          <div className="border-t border-slate-200 px-4 py-3 bg-white">
            <div className="flex gap-2">
              <Textarea
                data-testid="coach-input"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
                placeholder="Type honestly. The coach won't be polite."
                rows={2}
                className="flex-1 resize-none"
                disabled={sending}
              />
              <Button
                data-testid="coach-send-btn"
                onClick={sendMessage}
                disabled={sending || !draft.trim()}
                className="bg-slate-900 hover:bg-slate-800 text-white px-4"
              >
                {sending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </Button>
            </div>
            <div className="text-xs text-slate-400 mt-2">
              Press Enter to send. Shift+Enter for a new line.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Bubble({ role, content, streaming }) {
  const isUser = role === "user";
  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="w-9 h-9 rounded-full bg-amber-500 flex-shrink-0 flex items-center justify-center text-slate-900 font-bold text-sm">
          M
        </div>
      )}
      <div
        className={[
          "max-w-[80%] rounded-2xl px-4 py-3 leading-relaxed whitespace-pre-wrap break-words",
          isUser
            ? "bg-slate-900 text-white rounded-tr-sm"
            : "bg-slate-100 text-slate-900 rounded-tl-sm",
        ].join(" ")}
      >
        {content}
        {streaming && (
          <span className="inline-block w-2 h-4 bg-slate-400 ml-1 animate-pulse align-text-bottom" />
        )}
      </div>
      {isUser && (
        <div className="w-9 h-9 rounded-full bg-slate-300 flex-shrink-0 flex items-center justify-center text-slate-700 font-bold text-sm">
          You
        </div>
      )}
    </div>
  );
}
