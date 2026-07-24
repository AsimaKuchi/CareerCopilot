// FeaturePreviews.jsx
// "See it in action" section for the landing page. Renders visual mockups of
// the five core product surfaces in tasteful browser/window chrome so
// visitors can preview the product before signing up. All content is HTML/CSS
// (no screenshots) so previews never go stale.

import { useState, useEffect, useRef } from "react";
import {
  Chrome,
  FileText,
  MessageSquareText,
  LayoutGrid,
  Sparkles,
  CheckCircle2,
  HelpCircle,
  Building2,
  ArrowUpRight,
  TrendingUp,
} from "lucide-react";

// -- Shared: a compact browser/window chrome wrapper for each preview
function WindowChrome({ title = "", children, dark = false, testid }) {
  return (
    <div
      data-testid={testid}
      className={`rounded-2xl overflow-hidden shadow-xl ring-1 ${
        dark
          ? "ring-white/10 bg-[#1e1b4b]"
          : "ring-gray-200 bg-white"
      }`}
    >
      <div
        className={`flex items-center gap-1.5 px-3.5 py-2.5 border-b ${
          dark ? "border-white/10 bg-black/20" : "border-gray-100 bg-gray-50"
        }`}
      >
        <span className="w-2.5 h-2.5 rounded-full bg-[#ff5f56]" />
        <span className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]" />
        <span className="w-2.5 h-2.5 rounded-full bg-[#27c93f]" />
        {title && (
          <span
            className={`ml-3 text-[11px] font-medium ${
              dark ? "text-white/50" : "text-gray-400"
            }`}
          >
            {title}
          </span>
        )}
      </div>
      <div className={dark ? "text-white" : "text-gray-900"}>{children}</div>
    </div>
  );
}

// -- Preview 1: Chrome extension Field Coverage Report
function ExtensionPreview() {
  return (
    <WindowChrome
      testid="preview-extension"
      dark
      title="MyCareerCoPilot · Extension"
    >
      <div className="p-4 space-y-3 min-h-[320px]">
        {/* User row */}
        <div className="rounded-lg bg-white/5 px-3 py-2">
          <p className="text-[11px] text-white/50">Signed in as</p>
          <p className="text-xs font-medium">fuzailbukhari@gmail.com</p>
        </div>

        {/* Coverage summary card */}
        <div className="rounded-lg bg-white/[0.06] border border-white/10 p-3">
          <div className="flex items-baseline justify-between">
            <span className="text-xs font-semibold">6 / 8 filled</span>
            <span
              className="text-lg font-bold"
              style={{
                background: "linear-gradient(135deg,#6ee7b7,#10b981)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              75%
            </span>
          </div>
          <div className="mt-2 h-1.5 rounded-full bg-white/10 overflow-hidden">
            <div
              className="h-full rounded-full"
              style={{
                width: "75%",
                background: "linear-gradient(90deg,#10b981,#34d399)",
              }}
            />
          </div>
          <p className="mt-2 text-[10px] text-amber-300">
            2 fields need your attention below
          </p>
        </div>

        {/* Groups */}
        {[
          {
            label: "PERSONAL INFO",
            items: [
              { name: "First Name", ok: true },
              { name: "Email", ok: true },
              { name: "Phone", ok: true },
            ],
          },
          {
            label: "DOCUMENTS",
            items: [
              { name: "Resume (optimized for this job)", ok: true },
              {
                name: "Cover Letter",
                ok: false,
                hint: "No file input — attach manually",
              },
            ],
          },
          {
            label: "SCREENING",
            items: [
              { name: "Country of residence", ok: true, hint: "Selected: Canada" },
              { name: "Gender", ok: false, hint: "EEO — please answer manually" },
            ],
          },
        ].map((g) => (
          <div key={g.label}>
            <p className="text-[10px] font-semibold tracking-wider text-white/40 mb-1">
              {g.label}
            </p>
            <div className="space-y-1">
              {g.items.map((it) => (
                <div
                  key={it.name}
                  className={`flex items-start gap-2 rounded-md px-2 py-1.5 border ${
                    it.ok
                      ? "bg-emerald-500/10 border-emerald-500/30"
                      : "bg-amber-400/10 border-amber-400/30"
                  }`}
                >
                  <span
                    className={`shrink-0 w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold ${
                      it.ok
                        ? "bg-emerald-500 text-white"
                        : "bg-amber-400 text-[#1e1b4b]"
                    }`}
                  >
                    {it.ok ? "✓" : "?"}
                  </span>
                  <div className="min-w-0">
                    <p className="text-[11px] leading-tight">{it.name}</p>
                    {it.hint && (
                      <p className="text-[10px] text-white/50 leading-tight mt-0.5">
                        {it.hint}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </WindowChrome>
  );
}

// -- Preview 2: AI Resume Optimizer
function ResumePreview() {
  return (
    <WindowChrome testid="preview-resume" title="Resume · Senior Data Engineer at Lyft">
      <div className="p-4 min-h-[320px] grid grid-cols-5 gap-4">
        {/* Fake resume paper */}
        <div className="col-span-3 rounded-lg border border-gray-200 bg-gradient-to-b from-white to-gray-50 p-3.5 text-[10px] leading-[1.4]">
          <div className="text-center border-b border-gray-200 pb-2 mb-2">
            <p className="text-[11px] font-bold text-gray-900">FUZAIL BUKHARI</p>
            <p className="text-[9px] text-gray-500">
              Toronto, ON · fuzailbukhari@gmail.com
            </p>
          </div>
          <p className="text-[9px] font-bold text-gray-800 mb-1">EXPERIENCE</p>
          <p className="font-semibold text-gray-900">Senior Data Engineer</p>
          <p className="text-gray-500 mb-1">Shopify · 2022–Present</p>
          <p className="text-gray-700">
            Built{" "}
            <span className="bg-emerald-100 text-emerald-800 px-0.5 rounded">
              real-time streaming pipelines
            </span>{" "}
            processing 2B+ events/day using{" "}
            <span className="bg-emerald-100 text-emerald-800 px-0.5 rounded">
              Kafka, Spark, Airflow
            </span>
            .
          </p>
          <p className="text-gray-700 mt-1">
            Migrated legacy ETL to{" "}
            <span className="bg-emerald-100 text-emerald-800 px-0.5 rounded">
              dbt + Snowflake
            </span>{" "}
            cutting run-time 68%.
          </p>
          <p className="text-gray-700 mt-1">
            Mentored 4 junior engineers; led design reviews for{" "}
            <span className="bg-emerald-100 text-emerald-800 px-0.5 rounded">
              rideshare-scale
            </span>{" "}
            data models.
          </p>
          <p className="text-[9px] font-bold text-gray-800 mt-2 mb-1">
            SKILLS
          </p>
          <p className="text-gray-700">
            Python, SQL, Kafka, Spark, Airflow, dbt, Snowflake, AWS
          </p>
        </div>

        {/* Score + suggestions */}
        <div className="col-span-2 space-y-2.5">
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-2.5">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-medium text-emerald-800">
                Job match
              </p>
              <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
            </div>
            <p className="text-2xl font-bold text-emerald-700 leading-none mt-1">
              92%
            </p>
            <p className="text-[10px] text-emerald-700/80 mt-1">
              +37 pts vs base resume
            </p>
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-2.5">
            <p className="text-[10px] font-semibold text-gray-800 mb-1.5">
              AI suggestions
            </p>
            <ul className="space-y-1">
              {[
                "Added: rideshare-scale data models",
                "Emphasized: real-time streaming",
                "Reworded: mentored → led design reviews",
              ].map((s) => (
                <li key={s} className="flex items-start gap-1.5 text-[10px] text-gray-600 leading-tight">
                  <CheckCircle2 className="w-3 h-3 text-emerald-500 shrink-0 mt-0.5" />
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>

          <button className="w-full rounded-lg bg-indigo-500 text-white text-[10px] font-medium py-2 hover:bg-indigo-600 transition">
            Download tailored PDF
          </button>
        </div>
      </div>
    </WindowChrome>
  );
}

// -- Preview 3: Streaming Interview Prep (with animated pulse dot)
function InterviewPreview() {
  const [dots, setDots] = useState(1);
  const intervalRef = useRef(null);
  useEffect(() => {
    intervalRef.current = setInterval(() => setDots((d) => (d % 3) + 1), 450);
    return () => clearInterval(intervalRef.current);
  }, []);
  return (
    <WindowChrome testid="preview-interview" title="Interview Prep · Behavioral">
      <div className="p-4 min-h-[320px] space-y-2.5 bg-gradient-to-br from-slate-50 to-white">
        <div className="flex items-center gap-2 text-[10px] text-gray-500">
          <MessageSquareText className="w-3 h-3" />
          <span className="font-medium">Behavioural: Leadership</span>
          <span className="ml-auto flex items-center gap-1 text-emerald-600">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            Streaming
          </span>
        </div>

        {/* User bubble */}
        <div className="flex justify-end">
          <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-indigo-500 text-white px-3 py-2 text-[11px] leading-snug">
            Tell me about a time you led a project through ambiguity.
          </div>
        </div>

        {/* AI bubble */}
        <div className="flex gap-2">
          <div className="shrink-0 w-6 h-6 rounded-full bg-gradient-to-br from-indigo-500 to-fuchsia-500 flex items-center justify-center">
            <Sparkles className="w-3 h-3 text-white" />
          </div>
          <div className="max-w-[85%] rounded-2xl rounded-tl-sm bg-white border border-gray-200 px-3 py-2 text-[11px] leading-snug text-gray-800">
            <p className="font-medium mb-1">Structure it with STAR:</p>
            <p>
              <span className="font-semibold text-indigo-600">Situation.</span>{" "}
              Set the scene in 1 sentence — team, project, constraints.
            </p>
            <p className="mt-1">
              <span className="font-semibold text-indigo-600">Task.</span> What
              was the goal and who owned it{".".repeat(dots)}
              <span className="inline-block w-1 h-3 bg-indigo-500 ml-0.5 align-middle animate-pulse" />
            </p>
          </div>
        </div>

        {/* Suggested follow-ups */}
        <div className="pt-2 border-t border-gray-100">
          <p className="text-[10px] font-semibold text-gray-500 mb-1.5">
            Try next
          </p>
          <div className="flex flex-wrap gap-1.5">
            {["Ask for feedback on my answer", "Give me a curveball follow-up", "Score my response"].map(
              (t) => (
                <button
                  key={t}
                  className="text-[10px] px-2.5 py-1 rounded-full border border-gray-200 bg-white text-gray-700 hover:border-indigo-300 hover:text-indigo-600 transition"
                >
                  {t}
                </button>
              )
            )}
          </div>
        </div>
      </div>
    </WindowChrome>
  );
}

// -- Preview 4: Application tracker kanban
function TrackerPreview() {
  const cols = [
    {
      title: "Applied",
      tint: "bg-slate-100 text-slate-700",
      count: 4,
      cards: [
        { role: "Data Engineer", co: "Lyft", when: "2h ago" },
        { role: "Senior Analyst", co: "Shopify", when: "Yesterday" },
      ],
    },
    {
      title: "Interview",
      tint: "bg-amber-50 text-amber-700",
      count: 2,
      cards: [
        { role: "Backend Engineer", co: "Wealthsimple", when: "Round 2 · Thu" },
        { role: "Staff DE", co: "Airbnb", when: "Onsite · next week" },
      ],
    },
    {
      title: "Offer",
      tint: "bg-emerald-50 text-emerald-700",
      count: 1,
      cards: [{ role: "Data Platform Lead", co: "Ramp", when: "Deadline Fri" }],
    },
  ];
  return (
    <WindowChrome testid="preview-tracker" title="Applications · This week">
      <div className="p-4 min-h-[320px]">
        <div className="grid grid-cols-3 gap-3">
          {cols.map((c) => (
            <div key={c.title} className="min-w-0">
              <div className="flex items-center justify-between mb-2">
                <span
                  className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${c.tint}`}
                >
                  {c.title}
                </span>
                <span className="text-[10px] text-gray-400">{c.count}</span>
              </div>
              <div className="space-y-2">
                {c.cards.map((k) => (
                  <div
                    key={k.role + k.co}
                    className="rounded-lg border border-gray-200 bg-white p-2.5 hover:border-gray-300 transition"
                  >
                    <div className="flex items-center gap-1.5 text-[10px] text-gray-500">
                      <Building2 className="w-3 h-3" />
                      {k.co}
                    </div>
                    <p className="text-[11px] font-medium text-gray-900 mt-0.5 leading-tight">
                      {k.role}
                    </p>
                    <p className="text-[10px] text-gray-400 mt-1">{k.when}</p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 rounded-lg bg-indigo-50 border border-indigo-100 p-2.5 flex items-center gap-2">
          <Sparkles className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
          <p className="text-[11px] text-indigo-800">
            <span className="font-semibold">2 follow-ups due today.</span>{" "}
            Tap to open your reminder queue.
          </p>
        </div>
      </div>
    </WindowChrome>
  );
}

// -- Preview 5: AI Career Coach
function CoachPreview() {
  return (
    <WindowChrome testid="preview-coach" title="AI Career Coach">
      <div className="p-4 min-h-[320px] bg-gradient-to-b from-fuchsia-50/40 to-white space-y-2.5">
        <div className="flex gap-2">
          <div className="shrink-0 w-6 h-6 rounded-full bg-gradient-to-br from-fuchsia-500 to-indigo-500 flex items-center justify-center">
            <Sparkles className="w-3 h-3 text-white" />
          </div>
          <div className="max-w-[88%] rounded-2xl rounded-tl-sm bg-white border border-gray-200 px-3 py-2 text-[11px] leading-snug text-gray-800">
            You&apos;ve got strong DE fundamentals — but for the{" "}
            <span className="font-semibold">Ramp Staff DE</span> role, they&apos;ll
            probe SaaS-specific data modelling.
            <div className="mt-1.5 grid grid-cols-2 gap-1.5">
              <div className="rounded-md bg-indigo-50 border border-indigo-100 px-2 py-1 text-[10px] text-indigo-700">
                📚 Study MRR pipelines
              </div>
              <div className="rounded-md bg-indigo-50 border border-indigo-100 px-2 py-1 text-[10px] text-indigo-700">
                🧠 Practise cohort SQL
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-indigo-500 text-white px-3 py-2 text-[11px] leading-snug">
            Draft me a 2-week prep plan.
          </div>
        </div>

        <div className="flex gap-2">
          <div className="shrink-0 w-6 h-6 rounded-full bg-gradient-to-br from-fuchsia-500 to-indigo-500 flex items-center justify-center">
            <Sparkles className="w-3 h-3 text-white" />
          </div>
          <div className="max-w-[88%] rounded-2xl rounded-tl-sm bg-white border border-gray-200 px-3 py-2 text-[11px] leading-snug text-gray-800">
            <p className="font-semibold text-indigo-600 mb-1">Week 1 · Foundations</p>
            <ul className="space-y-0.5 text-gray-700 list-disc pl-4">
              <li>Mon: SaaS metrics deep-dive (2h)</li>
              <li>Wed: cohort analysis SQL drills</li>
              <li>Fri: mock system design — billing pipeline</li>
            </ul>
          </div>
        </div>

        <div className="pt-1 flex items-center gap-2 text-[10px] text-gray-400">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          Personalised to your resume · Powered by GPT
        </div>
      </div>
    </WindowChrome>
  );
}

// -- Section wrapper
export default function FeaturePreviews() {
  const previews = [
    {
      tag: "CHROME EXTENSION",
      icon: Chrome,
      title: "Field Coverage Report",
      copy:
        "Every autofill returns a per-field report — filled in green, needs-your-touch in amber — so you always know exactly what to review before hitting submit.",
      Preview: ExtensionPreview,
    },
    {
      tag: "AI DOCUMENTS",
      icon: FileText,
      title: "Resume & cover letter, tailored for every role",
      copy:
        "Paste any job description and we rewrite your resume to match — keyword-optimized, ATS-safe, and a match score that tells you when you're competitive.",
      Preview: ResumePreview,
    },
    {
      tag: "INTERVIEW PREP",
      icon: MessageSquareText,
      title: "Streaming mock interviews with real-time coaching",
      copy:
        "Practice behavioral and technical rounds with a GPT-powered interviewer that streams responses, scores your answers, and throws curveballs on demand.",
      Preview: InterviewPreview,
    },
    {
      tag: "APPLICATION TRACKER",
      icon: LayoutGrid,
      title: "Your entire job hunt on one board",
      copy:
        "Applied · Interview · Offer — automatically populated from the extension. Follow-up reminders, upcoming interviews, and offer deadlines all in one glance.",
      Preview: TrackerPreview,
    },
    {
      tag: "AI CAREER COACH",
      icon: Sparkles,
      title: "1:1 coaching that knows your resume",
      copy:
        "Ask about role fit, salary negotiation, career pivots, or interview prep. The coach reads your profile, the job description, and gives advice grounded in your actual background.",
      Preview: CoachPreview,
    },
  ];

  return (
    <section
      className="max-w-6xl mx-auto px-6 py-24"
      data-testid="feature-previews-section"
      id="feature-previews"
    >
      <div className="text-center mb-14 animate-fade-in">
        <div className="inline-flex items-center gap-2 bg-gray-900 text-white px-3 py-1.5 rounded-full text-xs font-medium mb-4">
          <Sparkles className="w-3.5 h-3.5" />
          See it in action
        </div>
        <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3 tracking-tight">
          Every part of your job hunt — in one place
        </h2>
        <p className="text-sm sm:text-base text-gray-500 max-w-2xl mx-auto">
          Five product surfaces working together so you spend less time on
          admin, and more time on the things that actually move the needle.
        </p>
      </div>

      <div className="space-y-16">
        {previews.map((p, i) => {
          const flip = i % 2 === 1;
          return (
            <div
              key={p.title}
              data-testid={`preview-row-${i}`}
              className={`grid md:grid-cols-2 gap-8 md:gap-12 items-center ${
                flip ? "md:[&>div:first-child]:order-2" : ""
              }`}
            >
              {/* Copy */}
              <div className="space-y-3">
                <div className="inline-flex items-center gap-2 text-[11px] font-semibold tracking-[0.14em] text-indigo-500">
                  <p.icon className="w-3.5 h-3.5" />
                  {p.tag}
                </div>
                <h3 className="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight leading-tight">
                  {p.title}
                </h3>
                <p className="text-sm sm:text-[15px] text-gray-500 leading-relaxed max-w-md">
                  {p.copy}
                </p>
                <div className="pt-2">
                  <a
                    href="#feature-previews"
                    onClick={(e) => e.preventDefault()}
                    className="inline-flex items-center gap-1 text-xs font-medium text-indigo-600 hover:text-indigo-700 group"
                  >
                    Learn more
                    <ArrowUpRight className="w-3 h-3 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                  </a>
                </div>
              </div>

              {/* Mockup */}
              <div className="relative">
                {/* subtle backdrop glow */}
                <div
                  aria-hidden
                  className="absolute -inset-4 rounded-3xl opacity-40 blur-2xl -z-10"
                  style={{
                    background:
                      "radial-gradient(closest-side, rgba(99,102,241,0.25), transparent 70%)",
                  }}
                />
                <p.Preview />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

export { ExtensionPreview, ResumePreview, InterviewPreview, TrackerPreview, CoachPreview };
