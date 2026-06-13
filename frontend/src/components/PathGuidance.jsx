import { useEffect, useState, useRef } from "react";
import { API } from "@/App";
import { apiFetch } from "@/utils/apiFetch";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  CheckCircle,
  CalendarDays,
  MessageSquare,
  Loader2,
  Send,
  Sparkles,
  RefreshCw,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { toast } from "sonner";

/**
 * PathGuidance — three-in-one panel mounted per expanded career path:
 *   1. Skill-gap checklist with persisted progress
 *   2. 30-day game plan (on-demand LLM generation, cached server-side)
 *   3. "Ask the Coach" - single-turn Q&A scoped to this path
 */
function SectionHeader({ id, idx, icon: Icon, label, accent, right, open, onToggle }) {
  return (
    <button
      onClick={onToggle}
      className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
      data-testid={`guidance-section-${id}-${idx}`}
    >
      <div className="flex items-center gap-2">
        <Icon className={`w-4 h-4 ${accent}`} />
        <span className="text-sm font-semibold text-foreground">{label}</span>
        {right}
      </div>
      {open ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
    </button>
  );
}

export default function PathGuidance({ path, idx }) {
  const skillsToLearn = path.skills_to_learn || [];
  const pathTitle = path.title;

  const [loading, setLoading] = useState(true);
  const [skillsChecked, setSkillsChecked] = useState([]);
  const [plan, setPlan] = useState(null);
  const [qna, setQna] = useState([]);

  // Section open/closed
  const [openSection, setOpenSection] = useState(null); // 'skills'|'plan'|'ask'|null

  // Plan state
  const [planLoading, setPlanLoading] = useState(false);

  // Ask state
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const qnaEndRef = useRef(null);

  // Load initial guidance state once per path
  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const r = await apiFetch(`${API}/paths/guidance?path_title=${encodeURIComponent(pathTitle)}`);
        if (r.ok) {
          const data = await r.json();
          if (cancelled) return;
          setSkillsChecked(data.skills_checked || []);
          setPlan(data.plan_30d || null);
          setQna(data.qna || []);
        }
      } catch {
        /* silent - panel will just render empty defaults */
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [pathTitle]);

  useEffect(() => {
    if (openSection === "ask" && qnaEndRef.current) {
      qnaEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [qna, openSection]);

  const toggleSkill = async (skill, currentlyChecked) => {
    // Optimistic update
    const next = currentlyChecked
      ? skillsChecked.filter((s) => s !== skill)
      : [...skillsChecked, skill];
    setSkillsChecked(next);
    try {
      const res = await apiFetch(`${API}/paths/guidance/skills`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          path_title: pathTitle,
          skill,
          checked: !currentlyChecked,
        }),
      });
      if (!res.ok) {
        setSkillsChecked(skillsChecked); // rollback
        toast.error("Couldn't save your progress");
      }
    } catch {
      setSkillsChecked(skillsChecked);
      toast.error("Couldn't save your progress");
    }
  };

  const generatePlan = async (force = false) => {
    setPlanLoading(true);
    try {
      const url = `${API}/paths/guidance/plan${force ? "?force=true" : ""}`;
      const res = await apiFetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path_title: pathTitle, path_data: path }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || "Couldn't generate plan");
        return;
      }
      const data = await res.json();
      setPlan(data);
    } catch {
      toast.error("Network error - couldn't generate plan");
    } finally {
      setPlanLoading(false);
    }
  };

  const askCoach = async () => {
    const q = question.trim();
    if (!q || asking) return;
    setAsking(true);
    setQuestion("");
    // Optimistic - show user's question immediately
    const optimistic = { question: q, answer: "", created_at: new Date().toISOString(), _pending: true };
    setQna((prev) => [...prev, optimistic]);
    try {
      const res = await apiFetch(`${API}/paths/guidance/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          path_title: pathTitle,
          question: q,
          path_data: path,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || "Coach failed to respond");
        setQna((prev) => prev.filter((p) => !p._pending));
        return;
      }
      const entry = await res.json();
      setQna((prev) => prev.map((p) => (p._pending ? entry : p)));
    } catch {
      setQna((prev) => prev.filter((p) => !p._pending));
      toast.error("Network error - couldn't ask coach");
    } finally {
      setAsking(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      askCoach();
    }
  };

  const progress = skillsToLearn.length
    ? Math.round((skillsChecked.filter((s) => skillsToLearn.includes(s)).length / skillsToLearn.length) * 100)
    : 0;

  if (loading) {
    return (
      <div className="border-t pt-4 flex items-center justify-center py-4 text-xs text-muted-foreground">
        <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Loading your guidance...
      </div>
    );
  }

  return (
    <div className="border-t pt-4 space-y-2" data-testid={`path-guidance-${idx}`}>
      <div className="flex items-center gap-2 mb-1">
        <Sparkles className="w-4 h-4 text-indigo-500" />
        <h4 className="text-sm font-semibold text-foreground">Your Roadmap</h4>
      </div>

      {/* ====== 1. Skill-gap checklist ====== */}
      <div className="border rounded-lg overflow-hidden">
        <SectionHeader
          id="skills"
          idx={idx}
          icon={CheckCircle}
          label="Skill Gap Checklist"
          accent="text-emerald-500"
          open={openSection === "skills"}
          onToggle={() => setOpenSection(openSection === "skills" ? null : "skills")}
          right={
            <span className="text-xs text-muted-foreground ml-1">
              {skillsChecked.filter((s) => skillsToLearn.includes(s)).length}/{skillsToLearn.length}
            </span>
          }
        />
        {openSection === "skills" && (
          <div className="p-4 space-y-3 bg-background" data-testid={`guidance-skills-panel-${idx}`}>
            {skillsToLearn.length === 0 ? (
              <p className="text-xs text-muted-foreground">No specific skills to learn — you&apos;re already a strong fit.</p>
            ) : (
              <>
                <div className="flex items-center gap-3">
                  <Progress value={progress} className="h-2 flex-1" />
                  <span className="text-xs font-medium text-muted-foreground w-8 text-right">{progress}%</span>
                </div>
                <ul className="space-y-2">
                  {skillsToLearn.map((skill, i) => {
                    const checked = skillsChecked.includes(skill);
                    return (
                      <li key={i} className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => toggleSkill(skill, checked)}
                          className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                          data-testid={`guidance-skill-checkbox-${idx}-${i}`}
                        />
                        <span className={`text-sm ${checked ? "line-through text-muted-foreground" : "text-foreground"}`}>
                          {skill}
                        </span>
                      </li>
                    );
                  })}
                </ul>
              </>
            )}
          </div>
        )}
      </div>

      {/* ====== 2. 30-Day Game Plan ====== */}
      <div className="border rounded-lg overflow-hidden">
        <SectionHeader
          id="plan"
          idx={idx}
          icon={CalendarDays}
          label="30-Day Game Plan"
          accent="text-indigo-500"
          open={openSection === "plan"}
          onToggle={() => setOpenSection(openSection === "plan" ? null : "plan")}
          right={plan ? <span className="text-xs text-emerald-600 ml-1">Ready</span> : null}
        />
        {openSection === "plan" && (
          <div className="p-4 space-y-3 bg-background" data-testid={`guidance-plan-panel-${idx}`}>
            {!plan && !planLoading && (
              <div className="text-center py-4">
                <p className="text-sm text-muted-foreground mb-3">Get a personalized 4-week sprint to land this role.</p>
                <Button
                  size="sm"
                  onClick={() => generatePlan(false)}
                  className="bg-indigo-500 hover:bg-indigo-600"
                  data-testid={`guidance-generate-plan-${idx}`}
                >
                  <Sparkles className="w-4 h-4 mr-2" />Generate my plan
                </Button>
              </div>
            )}

            {planLoading && (
              <div className="flex items-center justify-center py-6 text-xs text-muted-foreground">
                <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Building your 30-day plan...
              </div>
            )}

            {plan && !planLoading && (
              <div className="space-y-4">
                {plan.headline && (
                  <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-3">
                    <p className="text-sm text-indigo-900 font-medium leading-snug">{plan.headline}</p>
                  </div>
                )}

                <div className="space-y-3">
                  {(plan.weeks || []).map((wk, i) => (
                    <div key={i} className="border rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="shrink-0 w-7 h-7 rounded-full bg-indigo-600 text-white text-xs flex items-center justify-center font-bold">
                          W{wk.week ?? i + 1}
                        </span>
                        <span className="font-semibold text-sm text-foreground">{wk.focus}</span>
                      </div>
                      <ul className="space-y-1.5 pl-9">
                        {(wk.tasks || []).map((t, j) => (
                          <li key={j} className="text-xs text-muted-foreground flex gap-1.5">
                            <span className="text-indigo-400 shrink-0">›</span>
                            <span>{t}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>

                {plan.success_signal && (
                  <div className="bg-emerald-50 border border-emerald-100 rounded-lg p-3">
                    <p className="text-xs uppercase tracking-wider font-semibold text-emerald-700 mb-1">Success Signal</p>
                    <p className="text-sm text-emerald-900 leading-snug">{plan.success_signal}</p>
                  </div>
                )}

                <div className="flex justify-end">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => generatePlan(true)}
                    disabled={planLoading}
                    className="text-xs text-muted-foreground"
                    data-testid={`guidance-regen-plan-${idx}`}
                  >
                    <RefreshCw className="w-3 h-3 mr-1.5" /> Regenerate
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ====== 3. Ask the Coach ====== */}
      <div className="border rounded-lg overflow-hidden">
        <SectionHeader
          id="ask"
          idx={idx}
          icon={MessageSquare}
          label="Ask the Coach"
          accent="text-amber-500"
          open={openSection === "ask"}
          onToggle={() => setOpenSection(openSection === "ask" ? null : "ask")}
          right={qna.length > 0 ? <span className="text-xs text-muted-foreground ml-1">{qna.length} {qna.length === 1 ? "Q" : "Qs"}</span> : null}
        />
        {openSection === "ask" && (
          <div className="p-4 space-y-3 bg-background" data-testid={`guidance-ask-panel-${idx}`}>
            <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
              {qna.length === 0 && (
                <p className="text-xs text-muted-foreground italic">
                  Ask anything about this path — pay, transition difficulty, what to learn first, etc.
                </p>
              )}
              {qna.map((entry, i) => (
                <div key={i} className="space-y-2" data-testid={`guidance-qna-${idx}-${i}`}>
                  <div className="bg-gray-50 rounded-lg px-3 py-2 text-sm text-foreground">
                    <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold block mb-0.5">You</span>
                    {entry.question}
                  </div>
                  {entry._pending ? (
                    <div className="flex items-center text-xs text-muted-foreground gap-2 pl-2">
                      <Loader2 className="w-3 h-3 animate-spin" /> Coach is thinking...
                    </div>
                  ) : (
                    <div className="bg-amber-50 border border-amber-100 rounded-lg px-3 py-2 text-sm text-foreground whitespace-pre-wrap">
                      <span className="text-[10px] uppercase tracking-wider text-amber-700 font-semibold block mb-0.5">Coach</span>
                      {entry.answer}
                    </div>
                  )}
                </div>
              ))}
              <div ref={qnaEndRef} />
            </div>

            <div className="flex gap-2 items-end pt-2 border-t">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={onKeyDown}
                rows={2}
                placeholder="Ask the coach about this path..."
                disabled={asking}
                className="flex-1 text-sm border rounded-md px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-200"
                data-testid={`guidance-ask-input-${idx}`}
              />
              <Button
                onClick={askCoach}
                disabled={asking || !question.trim()}
                size="sm"
                className="bg-amber-500 hover:bg-amber-600 text-slate-900"
                data-testid={`guidance-ask-submit-${idx}`}
              >
                {asking ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
