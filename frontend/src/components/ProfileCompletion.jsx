/**
 * ProfileCompletion.jsx
 *
 * Sticky, always-visible tracker at the top of the Profile page that shows
 * which "important" fields are still missing and celebrates when the user
 * has completed everything.
 *
 * The scoring intentionally mirrors the backend calculation in
 * /app/backend/routes/dashboard_routes.py (get_dashboard_stats) so the
 * client-side % matches the Dashboard bento-grid "Profile Complete" figure:
 *   - resume uploaded ......... 40
 *   - at least 1 skill ........ 20
 *   - at least 1 job title .... 20
 *   - at least 1 location ..... 10
 *   - experience_years > 0 .... 10
 */
import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, Circle, Sparkles, PartyPopper } from "lucide-react";

const CHECKLIST = [
  {
    key: "resume",
    label: "Upload your resume",
    weight: 40,
    anchor: "resume-card",
    isDone: (p) => Boolean(p?.resume_filename || p?.resume_text),
  },
  {
    key: "skills",
    label: "Add at least one skill",
    weight: 20,
    anchor: "skills-card",
    isDone: (p) => Array.isArray(p?.skills) && p.skills.length > 0,
  },
  {
    key: "job_titles",
    label: "Add a preferred job title",
    weight: 20,
    anchor: "job-titles-card",
    isDone: (p) => Array.isArray(p?.job_titles) && p.job_titles.length > 0,
  },
  {
    key: "locations",
    label: "Add a preferred location",
    weight: 10,
    anchor: "locations-card",
    isDone: (p) =>
      Array.isArray(p?.preferred_locations) && p.preferred_locations.length > 0,
  },
  {
    key: "experience",
    label: "Set your years of experience",
    weight: 10,
    anchor: "experience-salary-card",
    isDone: (p) => Number(p?.experience_years) > 0,
  },
];

const scrollToCard = (testid) => {
  const el = document.querySelector(`[data-testid="${testid}"]`);
  if (!el) return;
  el.scrollIntoView({ behavior: "smooth", block: "start" });
  // Brief pulse to draw the eye
  el.classList.add("ring-2", "ring-indigo-400", "ring-offset-2");
  setTimeout(() => {
    el.classList.remove("ring-2", "ring-indigo-400", "ring-offset-2");
  }, 1400);
};

export default function ProfileCompletion({ profile }) {
  const results = CHECKLIST.map((c) => ({ ...c, done: c.isDone(profile) }));
  const completed = results.filter((r) => r.done);
  const remaining = results.filter((r) => !r.done);
  const percent = results.reduce((sum, r) => sum + (r.done ? r.weight : 0), 0);
  const isComplete = percent >= 100;

  const barColor = isComplete
    ? "bg-emerald-500"
    : percent >= 60
      ? "bg-indigo-500"
      : "bg-amber-500";

  return (
    <div
      className={`rounded-2xl border p-6 mb-6 transition-all animate-fade-in ${
        isComplete
          ? "border-emerald-200 bg-gradient-to-br from-emerald-50 to-white"
          : "border-slate-200 bg-white"
      }`}
      data-testid="profile-completion-card"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="flex items-start gap-3">
          <div
            className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
              isComplete
                ? "bg-emerald-100 text-emerald-600"
                : "bg-indigo-100 text-indigo-600"
            }`}
          >
            {isComplete ? (
              <PartyPopper className="w-5 h-5" />
            ) : (
              <Sparkles className="w-5 h-5" />
            )}
          </div>
          <div className="min-w-0">
            <h2 className="text-lg font-bold text-slate-900 leading-tight">
              {isComplete ? "You're all set!" : "Profile completeness"}
            </h2>
            <p className="text-sm text-slate-600 mt-0.5">
              {isComplete
                ? "Every important field is filled — you'll get the best job matches."
                : `${remaining.length} item${remaining.length === 1 ? "" : "s"} left to unlock better matches.`}
            </p>
          </div>
        </div>
        <div className="text-right flex-shrink-0">
          <div
            className={`text-3xl font-extrabold tabular-nums ${
              isComplete ? "text-emerald-600" : "text-slate-900"
            }`}
            data-testid="profile-completion-percent"
          >
            {percent}%
          </div>
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 -mt-1">
            {completed.length}/{results.length} done
          </div>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-2 bg-slate-100 rounded-full overflow-hidden mb-5">
        <motion.div
          className={`h-full ${barColor}`}
          initial={{ width: 0 }}
          animate={{ width: `${percent}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        />
      </div>

      {/* Success celebration */}
      <AnimatePresence>
        {isComplete && (
          <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="flex items-center gap-2 text-sm text-emerald-700 font-medium mb-3"
            data-testid="profile-completion-success"
          >
            <CheckCircle2 className="w-4 h-4" />
            Great work — your profile is ready to power resume tailoring,
            interview prep, and job matching.
          </motion.div>
        )}
      </AnimatePresence>

      {/* Checklist */}
      <ul className="grid sm:grid-cols-2 gap-2">
        {results.map((r) => (
          <li key={r.key}>
            <button
              type="button"
              onClick={() => !r.done && scrollToCard(r.anchor)}
              disabled={r.done}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all text-left ${
                r.done
                  ? "bg-emerald-50/60 text-emerald-800 cursor-default"
                  : "bg-slate-50 text-slate-700 hover:bg-indigo-50 hover:text-indigo-700 cursor-pointer"
              }`}
              data-testid={`completion-item-${r.key}`}
            >
              {r.done ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              ) : (
                <Circle className="w-4 h-4 text-slate-400 flex-shrink-0" />
              )}
              <span
                className={`flex-1 truncate ${r.done ? "line-through decoration-emerald-500/50" : "font-medium"}`}
              >
                {r.label}
              </span>
              <span
                className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                  r.done
                    ? "bg-emerald-100 text-emerald-700"
                    : "bg-white text-slate-500 border border-slate-200"
                }`}
              >
                +{r.weight}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
