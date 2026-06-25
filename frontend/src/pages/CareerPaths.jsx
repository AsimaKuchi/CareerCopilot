import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { API } from "@/App";
import { apiFetch } from "@/utils/apiFetch";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import Navbar from "@/components/Navbar";
import {
  Compass,
  TrendingUp,
  ArrowRight,
  Briefcase,
  GraduationCap,
  Clock,
  DollarSign,
  BarChart3,
  BookOpen,
  ExternalLink,
  RefreshCw,
  Loader2,
  AlertCircle,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Target,
  X,
  Zap,
} from "lucide-react";
import { toast } from "sonner";
import PathGuidance from "@/components/PathGuidance";

const DIFFICULTY_STYLE = {
  easy: "bg-emerald-100 text-emerald-700 border-emerald-200",
  moderate: "bg-amber-100 text-amber-700 border-amber-200",
  hard: "bg-rose-100 text-rose-700 border-rose-200",
};

const DEMAND_STYLE = {
  very_high: "text-emerald-600",
  high: "text-emerald-600",
  medium: "text-amber-600",
  low: "text-rose-600",
};

const CATEGORY_META = {
  current: { label: "Advance in Role", accent: "border-l-indigo-500" },
  adjacent: { label: "Easy Transition", accent: "border-l-emerald-500" },
  stretch: { label: "Stretch Goal", accent: "border-l-amber-500" },
};

export default function CareerPaths({ user }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);
  const [expandedIdx, setExpandedIdx] = useState(0);
  const [regenerating, setRegenerating] = useState(false);

  // Learning-resources modal
  const [lrOpen, setLrOpen] = useState(false);
  const [lrSkills, setLrSkills] = useState([]);
  const [lrData, setLrData] = useState(null);
  const [lrLoading, setLrLoading] = useState(false);
  const [lrPathTitle, setLrPathTitle] = useState("");

  // Jobs drawer
  const [jobsOpen, setJobsOpen] = useState(false);
  const [jobsData, setJobsData] = useState(null);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [jobsPathTitle, setJobsPathTitle] = useState("");

  useEffect(() => {
    // On mount: try to load cached analysis (free). If none exists, the page
    // renders the dual-entry choice screen instead of auto-generating.
    (async () => {
      try {
        const r = await apiFetch(`${API}/ai/career-paths/cached`);
        if (r.ok) {
          setAnalysis(await r.json());
        }
        // 404 = no cache yet -> fall through to choice screen
      } catch {
        /* network hiccup is fine - user can still pick from the choice screen */
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const fetchAnalysis = async (force = false) => {
    if (force) setRegenerating(true);
    else setLoading(true);
    setError(null);

    try {
      if (force) {
        await apiFetch(`${API}/ai/career-paths`, {
          method: "DELETE",
        });
      }

      const res = await apiFetch(`${API}/ai/career-paths`, {
        method: "POST",
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const detail = body.detail;
        throw new Error(typeof detail === 'object' ? detail?.message : detail || "Failed to generate career analysis");
      }

      setAnalysis(await res.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setRegenerating(false);
    }
  };

  const openLearningResources = async (path) => {
    setLrOpen(true);
    setLrPathTitle(path.title);
    setLrSkills(path.skills_to_learn || []);
    setLrData(null);
    setLrLoading(true);

    try {
      const q = (path.skills_to_learn || []).join(",");
      const res = await fetch(
        `${API}/ai/learning-resources?skills=${encodeURIComponent(q)}`,
        { credentials: "include" }
      );
      if (res.ok) setLrData(await res.json());
    } catch {
      /* silent */
    } finally {
      setLrLoading(false);
    }
  };

  const openJobs = async (path) => {
    setJobsOpen(true);
    setJobsPathTitle(path.title);
    setJobsData(null);
    setJobsLoading(true);

    try {
      const loc = analysis?.user_location || "";
      const res = await fetch(
        `${API}/ai/career-paths/${encodeURIComponent(path.title)}/jobs?location=${encodeURIComponent(loc)}&min_match_score=50`,
        { credentials: "include" }
      );
      if (res.ok) setJobsData(await res.json());
    } catch {
      /* silent */
    } finally {
      setJobsLoading(false);
    }
  };

  /* ---- render helpers ---- */
  const toggle = (i) => setExpandedIdx(expandedIdx === i ? -1 : i);

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar user={user} />
        <div className="flex flex-col items-center justify-center py-32 gap-4">
          <Loader2 className="w-10 h-10 text-indigo-500 animate-spin" />
          <p className="text-muted-foreground text-sm">Loading your career analysis…</p>
        </div>
      </div>
    );
  }

  // No analysis on file yet -> show the dual-entry choice screen
  if (!analysis && !error) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar user={user} />
        <div className="max-w-5xl mx-auto px-4 py-12">
          <div className="text-center mb-10">
            <Compass className="w-12 h-12 text-indigo-500 mx-auto mb-4" />
            <h1 className="text-3xl sm:text-4xl font-bold text-foreground tracking-tight">
              Where do you want to go next?
            </h1>
            <p className="text-muted-foreground mt-4 max-w-2xl mx-auto leading-relaxed">
              Wondering if you&apos;re in the right career? Curious what else you could do with your skills?
            </p>
            <div className="mt-5 max-w-2xl mx-auto text-left bg-indigo-50/60 border border-indigo-100 rounded-xl px-5 py-4">
              <p className="text-sm text-foreground mb-3">
                This page maps your resume against real career paths in the market. You&apos;ll get:
              </p>
              <ul className="space-y-2 text-sm text-foreground/90">
                <li className="flex gap-2.5">
                  <span className="text-indigo-500 mt-0.5">›</span>
                  <span>
                    <strong className="font-semibold">3-5 best-fit career paths</strong> — with match scores, salary ranges, and difficulty
                  </span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-indigo-500 mt-0.5">›</span>
                  <span>
                    <strong className="font-semibold">A 30-day game plan</strong> for each path — concrete weekly tasks to start moving today
                  </span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-indigo-500 mt-0.5">›</span>
                  <span>
                    <strong className="font-semibold">An AI coach</strong> that answers your questions and pressure-tests your thinking
                  </span>
                </li>
              </ul>
            </div>
            <p className="text-muted-foreground mt-5 text-sm">
              Pick a starting point below.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 gap-5">
            {/* Path A: Knows where they want to go */}
            <Card
              data-testid="entry-tailored-btn"
              className="cursor-pointer hover:border-indigo-400 hover:shadow-lg transition-all border-2"
              onClick={() => fetchAnalysis(false)}
            >
              <CardContent className="pt-7 pb-6 space-y-3 text-center">
                <div className="w-12 h-12 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center mx-auto">
                  <Target className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold text-foreground">What could I actually do?</h3>
                <p className="text-sm text-muted-foreground">
                  We&apos;ll analyze your resume and show you the careers that fit — including ones you probably haven&apos;t considered. Browse, compare, see what catches your eye.
                </p>
                <Button
                  className="w-full mt-3 bg-indigo-500 hover:bg-indigo-600"
                  onClick={(e) => {
                    e.stopPropagation();
                    fetchAnalysis(false);
                  }}
                >
                  Show me what fits <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </CardContent>
            </Card>

            {/* Path B: Not sure - talk to the coach */}
            <Card
              data-testid="entry-coach-btn"
              className="cursor-pointer hover:border-amber-400 hover:shadow-lg transition-all border-2"
              onClick={() => navigate("/coach")}
            >
              <CardContent className="pt-7 pb-6 space-y-3 text-center">
                <div className="w-12 h-12 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center mx-auto">
                  <Zap className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold text-foreground">Help me figure it out</h3>
                <p className="text-sm text-muted-foreground">
                  Talk to an AI coach that asks sharp questions instead of giving you a list. They&apos;ll shape 3 paths around how you actually answer.
                </p>
                <Button
                  className="w-full mt-3 bg-amber-500 hover:bg-amber-600 text-slate-900 font-semibold"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate("/coach");
                  }}
                >
                  Talk to the coach <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </CardContent>
            </Card>
          </div>

          <p className="text-xs text-muted-foreground text-center mt-8">
            Either choice uses 1 of your monthly career analysis credits.
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar user={user} />
        <div className="max-w-xl mx-auto px-4 py-20">
          <Card className="border-rose-200 bg-rose-50/50">
            <CardContent className="pt-6 text-center space-y-4">
              <AlertCircle className="w-12 h-12 text-rose-500 mx-auto" />
              <h2 className="text-lg font-semibold text-rose-800">Unable to Analyze Career Paths</h2>
              <p className="text-sm text-rose-700">{error}</p>
              <div className="flex justify-center gap-3 pt-2">
                <Button variant="outline" onClick={() => navigate("/profile")} data-testid="go-to-profile-btn">
                  Complete Profile
                </Button>
                <Button onClick={() => fetchAnalysis()} data-testid="retry-analysis-btn">
                  Try Again
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  const paths = analysis?.recommended_paths || [];
  const current = analysis?.current_path;

  return (
    <div className="min-h-screen bg-background">
      <Navbar user={user} />

      <div className="max-w-5xl mx-auto px-4 py-8 space-y-6" data-testid="career-paths-page">
        {/* ---- Header ---- */}
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-foreground tracking-tight flex items-center gap-2">
              <Compass className="w-7 h-7 text-indigo-500" />
              Career Path Analysis
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Based on your resume, skills &amp; {analysis?.experience_years ?? "?"} years of experience
            </p>
          </div>
          <div className="flex gap-2 flex-wrap">
            <Button
              variant="ghost"
              size="sm"
              onClick={async () => {
                if (!window.confirm("Clear your current analysis and return to the start screen? You'll be asked again how you'd like to explore.")) return;
                try {
                  await apiFetch(`${API}/ai/career-paths`, { method: "DELETE" });
                  setAnalysis(null);
                  setExpandedIdx(0);
                  toast.success("Analysis cleared - pick a new starting point");
                } catch {
                  toast.error("Couldn't reset - try again");
                }
              }}
              data-testid="start-over-btn"
              className="text-muted-foreground hover:text-foreground"
            >
              <X className="w-4 h-4 mr-2" />
              Start over
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate("/coach")}
              data-testid="open-coach-btn"
              className="border-amber-300 text-amber-700 hover:bg-amber-50"
            >
              <Zap className="w-4 h-4 mr-2" />
              Talk to Coach
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={regenerating}
              onClick={() => fetchAnalysis(true)}
              data-testid="regenerate-btn"
            >
              {regenerating ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-2" />}
              Regenerate
            </Button>
          </div>
        </div>

        {/* ---- Current Path Banner ---- */}
        {current && (
          <Card className="bg-gradient-to-br from-indigo-600 to-violet-600 text-white border-0 shadow-lg" data-testid="current-path-card">
            <CardContent className="py-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <p className="text-indigo-200 text-xs font-medium uppercase tracking-wider mb-1">Current Path</p>
                <h2 className="text-2xl sm:text-3xl font-bold">{current.title}</h2>
                <p className="text-indigo-100 text-sm mt-1">
                  Avg. salary <span className="font-semibold">${(current.salary_avg ?? 0).toLocaleString()}</span>/yr
                </p>
              </div>
              <div className="flex gap-6 text-sm">
                <div className="text-center">
                  <p className="text-indigo-200 text-xs">Demand</p>
                  <p className="font-semibold capitalize">{(current.market_demand || "").replace("_", " ")}</p>
                </div>
                <div className="text-center">
                  <p className="text-indigo-200 text-xs">Security</p>
                  <p className="font-semibold capitalize">{current.job_security}</p>
                </div>
                <div className="text-center">
                  <p className="text-indigo-200 text-xs">Growth</p>
                  <p className="font-semibold capitalize">{current.growth_potential}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* ---- Recommended Paths ---- */}
        <h2 className="text-lg font-semibold text-foreground pt-2">Recommended Paths</h2>

        <div className="space-y-4">
          {paths.map((path, i) => {
            const meta = CATEGORY_META[path.category] || CATEGORY_META.adjacent;
            const expanded = expandedIdx === i;
            const sal = path.salary_range || {};

            return (
              <Card
                key={i}
                className={`border-l-4 ${meta.accent} transition-shadow hover:shadow-md`}
                data-testid={`career-path-card-${i}`}
              >
                {/* Collapsed header — always visible */}
                <button
                  onClick={() => toggle(i)}
                  className="w-full text-left px-5 py-4 flex items-center justify-between gap-4"
                  data-testid={`career-path-toggle-${i}`}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <span className="font-bold text-lg text-foreground truncate">{path.title}</span>
                      <Badge variant="outline" className={`text-xs ${DIFFICULTY_STYLE[path.difficulty] || ""}`}>
                        {path.difficulty}
                      </Badge>
                      <Badge variant="secondary" className="text-xs">{meta.label}</Badge>
                    </div>
                    <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1"><DollarSign className="w-3 h-3" />${(sal.avg ?? 0).toLocaleString()}/yr</span>
                      <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{path.time_to_transition}</span>
                      <span className={`flex items-center gap-1 font-medium capitalize ${DEMAND_STYLE[path.market_demand] || ""}`}>
                        <BarChart3 className="w-3 h-3" />{(path.market_demand || "").replace("_", " ")} demand
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <div className="text-center">
                      <p className="text-2xl font-bold text-indigo-600">{path.match_score}%</p>
                      <p className="text-[10px] text-muted-foreground leading-none">match</p>
                    </div>
                    {expanded ? <ChevronUp className="w-5 h-5 text-muted-foreground" /> : <ChevronDown className="w-5 h-5 text-muted-foreground" />}
                  </div>
                </button>

                {/* Expanded details */}
                {expanded && (
                  <CardContent className="pt-0 pb-5 px-5 space-y-5 border-t">
                    {/* Salary bar */}
                    <div className="pt-4">
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span className="text-muted-foreground">Salary range</span>
                        <span className="font-semibold text-emerald-600">{path.salary_increase}</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-muted-foreground">${(sal.min ?? 0).toLocaleString()}</span>
                        <div className="flex-1 h-2 rounded-full bg-gray-100 overflow-hidden">
                          <div
                            className="h-full rounded-full bg-gradient-to-r from-indigo-400 to-indigo-600"
                            style={{ width: `${Math.min(100, ((sal.avg - sal.min) / (sal.max - sal.min || 1)) * 100)}%` }}
                          />
                        </div>
                        <span className="text-muted-foreground">${(sal.max ?? 0).toLocaleString()}</span>
                      </div>
                    </div>

                    {/* Skills grid */}
                    <div className="grid sm:grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm font-medium text-foreground mb-2 flex items-center gap-1.5">
                          <CheckCircle className="w-4 h-4 text-emerald-500" />Skills You Have
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {(path.skills_you_have || []).map((s, j) => (
                            <Badge key={j} variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200 text-xs">{s}</Badge>
                          ))}
                        </div>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-foreground mb-2 flex items-center gap-1.5">
                          <GraduationCap className="w-4 h-4 text-blue-500" />Skills to Learn
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {(path.skills_to_learn || []).map((s, j) => (
                            <Badge key={j} variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 text-xs">{s}</Badge>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Reasoning */}
                    <div className="bg-gray-50 rounded-lg p-4 text-sm text-muted-foreground">
                      <p className="font-medium text-foreground mb-1">Why this path?</p>
                      {path.reasoning}
                    </div>

                    {/* Next steps */}
                    {path.next_steps?.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-foreground mb-2">Next Steps</p>
                        <ol className="space-y-2">
                          {path.next_steps.map((step, j) => (
                            <li key={j} className="flex items-start gap-2 text-sm text-muted-foreground">
                              <span className="shrink-0 w-5 h-5 rounded-full bg-indigo-600 text-white text-xs flex items-center justify-center mt-0.5">{j + 1}</span>
                              {step}
                            </li>
                          ))}
                        </ol>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex flex-col sm:flex-row gap-2 pt-2">
                      <Button
                        className="flex-1"
                        onClick={() => openLearningResources(path)}
                        data-testid={`learn-btn-${i}`}
                      >
                        <BookOpen className="w-4 h-4 mr-2" />Learning Resources
                      </Button>
                      <Button
                        variant="outline"
                        className="flex-1"
                        onClick={() => openJobs(path)}
                        data-testid={`jobs-btn-${i}`}
                      >
                        <Briefcase className="w-4 h-4 mr-2" />View Matching Jobs
                      </Button>
                    </div>

                    {/* Guidance Triplet: skills checklist + 30-day plan + ask the coach */}
                    <PathGuidance path={path} idx={i} />
                  </CardContent>
                )}
              </Card>
            );
          })}
        </div>
      </div>

      {/* ======= Learning Resources Modal ======= */}
      {lrOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" data-testid="lr-modal">
          <div className="bg-background rounded-xl shadow-2xl w-full max-w-2xl max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between px-5 py-4 border-b">
              <h2 className="font-bold text-lg truncate">Resources for {lrPathTitle}</h2>
              <button onClick={() => setLrOpen(false)} className="p-1 rounded hover:bg-accent"><X className="w-5 h-5" /></button>
            </div>
            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
              {lrLoading && (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
                </div>
              )}

              {!lrLoading && lrData && (
                <>
                  {/* Summary */}
                  <div className="grid grid-cols-3 gap-3 text-center text-sm">
                    <div className="bg-indigo-50 rounded-lg py-3">
                      <p className="text-xl font-bold text-indigo-600">{lrData.summary?.total_resources ?? 0}</p>
                      <p className="text-muted-foreground text-xs">Resources</p>
                    </div>
                    <div className="bg-emerald-50 rounded-lg py-3">
                      <p className="text-xl font-bold text-emerald-600">{lrData.summary?.free_resources ?? 0}</p>
                      <p className="text-muted-foreground text-xs">Free</p>
                    </div>
                    <div className="bg-amber-50 rounded-lg py-3">
                      <p className="text-xl font-bold text-amber-600">{lrData.summary?.total_hours ?? 0}h</p>
                      <p className="text-muted-foreground text-xs">Total Time</p>
                    </div>
                  </div>

                  {/* Per-skill resources */}
                  {Object.entries(lrData.resources || {}).map(([skill, resources]) => (
                    <div key={skill} className="border rounded-lg">
                      <div className="px-4 py-3 bg-gray-50 border-b font-medium text-sm">{skill}</div>
                      <div className="divide-y">
                        {resources.map((r, j) => (
                          <div key={j} className="px-4 py-3 flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <p className="font-medium text-sm truncate">{r.title}</p>
                              <p className="text-xs text-muted-foreground">{r.provider} · {r.duration_hours}h · {r.cost}</p>
                            </div>
                            <a href={r.url} target="_blank" rel="noopener noreferrer" className="shrink-0">
                              <Button size="sm" variant="ghost"><ExternalLink className="w-4 h-4" /></Button>
                            </a>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}

                  {/* Skills without resources */}
                  {lrSkills.filter(s => !lrData.resources?.[s]).length > 0 && (
                    <div className="text-sm text-muted-foreground bg-gray-50 rounded-lg p-4">
                      <p className="font-medium text-foreground mb-1">No curated resources yet for:</p>
                      <p>{lrSkills.filter(s => !lrData.resources?.[s]).join(", ")}</p>
                      <p className="mt-1 text-xs">Try searching these on Coursera, Udemy, or YouTube.</p>
                    </div>
                  )}
                </>
              )}
            </div>
            <div className="px-5 py-3 border-t flex justify-end">
              <Button variant="outline" onClick={() => setLrOpen(false)}>Close</Button>
            </div>
          </div>
        </div>
      )}

      {/* ======= Jobs Drawer ======= */}
      {jobsOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" data-testid="jobs-modal">
          <div className="bg-background rounded-xl shadow-2xl w-full max-w-3xl max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between px-5 py-4 border-b">
              <h2 className="font-bold text-lg truncate">{jobsPathTitle} Jobs</h2>
              <button onClick={() => setJobsOpen(false)} className="p-1 rounded hover:bg-accent"><X className="w-5 h-5" /></button>
            </div>
            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
              {jobsLoading && (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
                </div>
              )}

              {!jobsLoading && jobsData && (
                <>
                  {/* Summary */}
                  <div className="grid grid-cols-4 gap-3 text-center text-sm">
                    <div className="bg-gray-50 rounded-lg py-3">
                      <p className="text-xl font-bold">{jobsData.total_jobs_found}</p>
                      <p className="text-muted-foreground text-xs">Found</p>
                    </div>
                    <div className="bg-emerald-50 rounded-lg py-3">
                      <p className="text-xl font-bold text-emerald-600">{jobsData.summary?.ready_to_apply_now ?? 0}</p>
                      <p className="text-muted-foreground text-xs">Ready</p>
                    </div>
                    <div className="bg-amber-50 rounded-lg py-3">
                      <p className="text-xl font-bold text-amber-600">{jobsData.summary?.close_match ?? 0}</p>
                      <p className="text-muted-foreground text-xs">Close</p>
                    </div>
                    <div className="bg-indigo-50 rounded-lg py-3">
                      <p className="text-xl font-bold text-indigo-600">{jobsData.summary?.avg_match_score ?? 0}%</p>
                      <p className="text-muted-foreground text-xs">Avg Match</p>
                    </div>
                  </div>

                  {/* Job list */}
                  {(jobsData.jobs || []).length === 0 && (
                    <p className="text-center text-muted-foreground py-8 text-sm">No matching jobs found in your area. Try broadening your search.</p>
                  )}

                  {(jobsData.jobs || []).map((item, j) => {
                    const job = item.job || {};
                    return (
                      <div key={j} className="border rounded-lg p-4 space-y-2">
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0 flex-1">
                            <p className="font-semibold text-sm truncate">{job.title}</p>
                            <p className="text-xs text-muted-foreground">{job.company} · {job.location}</p>
                          </div>
                          <div className="text-right shrink-0">
                            <p className={`text-lg font-bold ${item.match_score >= 75 ? "text-emerald-600" : item.match_score >= 65 ? "text-amber-600" : "text-muted-foreground"}`}>
                              {item.match_score}%
                            </p>
                            {item.ready_to_apply && <Badge className="bg-emerald-100 text-emerald-700 border-0 text-[10px]">Ready</Badge>}
                          </div>
                        </div>

                        {(item.strengths?.length > 0 || item.gaps?.length > 0) && (
                          <div className="flex flex-wrap gap-1 text-xs">
                            {item.strengths?.slice(0, 2).map((s, k) => (
                              <span key={k} className="text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded">{s.length > 60 ? s.slice(0, 57) + "…" : s}</span>
                            ))}
                            {item.gaps?.slice(0, 1).map((g, k) => (
                              <span key={k} className="text-rose-600 bg-rose-50 px-2 py-0.5 rounded">{g.length > 60 ? g.slice(0, 57) + "…" : g}</span>
                            ))}
                          </div>
                        )}

                        {job.apply_link && (
                          <a href={job.apply_link} target="_blank" rel="noopener noreferrer">
                            <Button size="sm" variant="outline" className="mt-1">
                              <ExternalLink className="w-3 h-3 mr-1.5" />Apply
                            </Button>
                          </a>
                        )}
                      </div>
                    );
                  })}
                </>
              )}
            </div>
            <div className="px-5 py-3 border-t flex justify-end">
              <Button variant="outline" onClick={() => setJobsOpen(false)}>Close</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
