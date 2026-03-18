import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion, useInView } from "framer-motion";
import { API } from "@/App";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import Navbar from "@/components/Navbar";
import FormattedJobDescription from "@/components/FormattedJobDescription";
import { getDisplaySalary } from "@/utils/extractSalary";
import {
  Briefcase,
  FileText,
  Target,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  ArrowRight,
  Search,
  Sparkles,
  Star,
  MapPin,
  Building,
  ExternalLink,
  DollarSign,
  Timer,
  Zap,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { toast } from "sonner";

/* ─── Animated Counter ─── */
function AnimatedNumber({ value, suffix = "", duration = 1200 }) {
  const [display, setDisplay] = useState(0);
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });

  useEffect(() => {
    if (!inView) return;
    const num = typeof value === "number" ? value : parseFloat(value) || 0;
    if (num === 0) { setDisplay(0); return; }
    const start = performance.now();
    const step = (now) => {
      const t = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - t, 3);
      setDisplay(Math.round(ease * num * 10) / 10);
      if (t < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [inView, value, duration]);

  return <span ref={ref}>{Number.isInteger(value) ? Math.round(display) : display.toFixed(1)}{suffix}</span>;
}

/* ─── Mini Sparkline ─── */
function Sparkline({ total }) {
  const count = 14;
  const data = useRef(
    Array.from({ length: count }, (_, i) => {
      const base = Math.max(1, total - count + i + 1);
      return base + Math.round((Math.random() - 0.35) * Math.max(1, base * 0.2));
    }).map(v => Math.max(0, v))
  ).current;

  const max = Math.max(...data, 1);
  const min = Math.min(...data);
  const h = 48, w = 180;
  const points = data.map((v, i) => {
    const x = (i / (count - 1)) * w;
    const y = h - ((v - min) / (max - min + 1)) * (h - 8) - 4;
    return `${x},${y}`;
  });
  const line = points.join(" ");
  const area = `0,${h} ${line} ${w},${h}`;

  return (
    <svg width={w} height={h} className="overflow-visible">
      <defs>
        <linearGradient id="spark-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgba(255,255,255,0.25)" />
          <stop offset="100%" stopColor="rgba(255,255,255,0.02)" />
        </linearGradient>
      </defs>
      <polygon points={area} fill="url(#spark-fill)" />
      <polyline
        points={line}
        fill="none"
        stroke="rgba(255,255,255,0.7)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx={points.at(-1).split(",")[0]} cy={points.at(-1).split(",")[1]} r="3" fill="white" />
    </svg>
  );
}

/* ─── Animated Progress Bar ─── */
function AnimatedBar({ value }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const [width, setWidth] = useState(0);

  useEffect(() => {
    if (inView) {
      const timer = setTimeout(() => setWidth(value), 100);
      return () => clearTimeout(timer);
    }
  }, [inView, value]);

  return (
    <div ref={ref} className="w-full h-2.5 rounded-full bg-gray-100 overflow-hidden">
      <motion.div
        className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500"
        initial={{ width: 0 }}
        animate={{ width: `${width}%` }}
        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
      />
    </div>
  );
}

/* ─── Time context message ─── */
function getTimeMessage(hours) {
  if (hours >= 80) return "That's an entire 2-week sprint saved!";
  if (hours >= 40) return "That's a full work week saved!";
  if (hours >= 16) return "That's almost 2 work days saved!";
  if (hours >= 8) return "That's a full work day saved!";
  if (hours >= 4) return "That's half a work day saved!";
  if (hours >= 1) return "Every hour counts — keep going!";
  return "You're just getting started!";
}

/* ─── Bento Stats ─── */
function BentoStats({ stats }) {
  const totalApps = stats?.total_applications || 0;
  const applied = stats?.applied || 0;
  const profilePct = stats?.profile_completeness || 0;
  const totalMinutes = stats?.time_saved?.total_minutes || 0;
  const totalHours = stats?.time_saved?.total_hours || (totalMinutes / 60);
  const timeDisplay = totalMinutes >= 60
    ? `${totalHours.toFixed(1)}h`
    : `${totalMinutes}m`;

  const card = (delay) => ({
    initial: { opacity: 0, y: 16 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.45, delay, ease: [0.22, 1, 0.36, 1] },
  });

  return (
    <div
      className="grid grid-cols-4 gap-4 mb-8"
      data-testid="bento-stats"
      style={{ gridTemplateRows: "auto auto" }}
    >
      {/* Total Applications — 2 cols, tall */}
      <motion.div
        {...card(0)}
        data-testid="stat-total"
        className="col-span-4 sm:col-span-2 row-span-1 relative overflow-hidden rounded-xl p-6 bg-gradient-to-br from-indigo-500 via-indigo-600 to-violet-600 shadow-md hover:shadow-lg transition-shadow duration-200"
      >
        <div className="relative z-10 flex flex-col justify-between h-full min-h-[140px]">
          <p className="text-sm font-medium text-indigo-100 tracking-wide">Total Applications</p>
          <div>
            <p className="text-5xl font-bold text-white tracking-tight leading-none">
              <AnimatedNumber value={totalApps} />
            </p>
            <p className="text-xs text-indigo-200 mt-2">
              {totalApps === 0 ? "Start applying to track progress" : "applications tracked"}
            </p>
          </div>
        </div>
        {/* Sparkline */}
        <div className="absolute bottom-4 right-4 opacity-80">
          <Sparkline total={totalApps} />
        </div>
        {/* Decorative circle */}
        <div className="absolute -top-12 -right-12 w-40 h-40 rounded-full bg-white/5" />
      </motion.div>

      {/* Applied — 1 col */}
      <motion.div
        {...card(0.05)}
        data-testid="stat-applied"
        className="col-span-2 sm:col-span-1 relative overflow-hidden rounded-xl p-6 bg-white border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-200"
      >
        <div className="flex flex-col justify-between h-full min-h-[140px]">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Applied</p>
            <div className="w-9 h-9 rounded-lg bg-emerald-50 flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-emerald-500" />
            </div>
          </div>
          <div>
            <p className="text-4xl font-bold text-gray-900 tracking-tight leading-none">
              <AnimatedNumber value={applied} />
            </p>
            <p className="text-xs text-gray-400 mt-2">applications sent</p>
          </div>
        </div>
      </motion.div>

      {/* Profile Complete — 1 col */}
      <motion.div
        {...card(0.1)}
        data-testid="stat-profile"
        className="col-span-2 sm:col-span-1 relative overflow-hidden rounded-xl p-6 bg-white border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-200"
      >
        <div className="flex flex-col justify-between h-full min-h-[140px]">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Profile Complete</p>
            <div className="w-9 h-9 rounded-lg bg-indigo-50 flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-indigo-500" />
            </div>
          </div>
          <div>
            <p className="text-4xl font-bold text-gray-900 tracking-tight leading-none">
              <AnimatedNumber value={profilePct} suffix="%" />
            </p>
            <div className="mt-3">
              <AnimatedBar value={profilePct} />
            </div>
          </div>
        </div>
      </motion.div>

      {/* Time Saved — full width bottom */}
      <motion.div
        {...card(0.15)}
        data-testid="stat-time-saved"
        className="col-span-4 relative overflow-hidden rounded-xl px-6 py-5 bg-gradient-to-r from-indigo-50 via-white to-violet-50 border border-indigo-100 shadow-sm hover:shadow-md transition-shadow duration-200"
      >
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-100 flex items-center justify-center">
              <Clock className="w-5 h-5 text-indigo-600" />
            </div>
            <div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-gray-900">
                  <AnimatedNumber value={parseFloat(totalHours.toFixed(1))} suffix="h" duration={1400} />
                </span>
                <span className="text-sm font-medium text-gray-500">saved</span>
              </div>
            </div>
          </div>
          <p className="text-sm text-gray-600 sm:text-right">
            {getTimeMessage(totalHours)}
          </p>
        </div>
      </motion.div>
    </div>
  );
}

export default function Dashboard({ user }) {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [savedJobs, setSavedJobs] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedJobId, setExpandedJobId] = useState(null);

  useEffect(() => {
    fetchStats();
    fetchSavedJobs();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API}/dashboard/stats`, {
        credentials: "include",
      });
      if (!response.ok) throw new Error("Failed to fetch stats");
      const data = await response.json();
      setStats(data);
    } catch (error) {
      toast.error("Failed to load dashboard stats");
    } finally {
      setLoading(false);
    }
  };

  const fetchSavedJobs = async () => {
    try {
      const response = await fetch(`${API}/jobs/saved`, {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        setSavedJobs(data);
      }
    } catch (error) {
      console.error("Failed to fetch saved jobs:", error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "applied":
        return "bg-emerald-50 text-emerald-700 border-emerald-200";
      case "pending":
        return "bg-amber-50 text-amber-700 border-amber-200";
      case "rejected":
        return "bg-red-50 text-red-700 border-red-200";
      default:
        return "bg-gray-50 text-gray-700 border-gray-200";
    }
  };

  const quickActions = [
    {
      icon: Search,
      label: "Find Jobs",
      description: "Search AI-matched opportunities",
      path: "/jobs",
      color: "from-indigo-500 to-indigo-600",
    },
    {
      icon: FileText,
      label: "Update Profile",
      description: "Optimize your resume",
      path: "/profile",
      color: "from-emerald-500 to-emerald-600",
    },
    {
      icon: Target,
      label: "Applications",
      description: "Track your progress",
      path: "/applications",
      color: "from-amber-500 to-amber-600",
    },
    {
      icon: Sparkles,
      label: "Interview Prep",
      description: "AI-powered preparation",
      path: "/interview-prep",
      color: "from-rose-500 to-rose-600",
    },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar user={user} />
        <main className="max-w-7xl mx-auto px-6 py-8">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
            {[1, 2, 3, 4].map((i) => (
              <Card key={i} className="glass-light animate-pulse">
                <CardContent className="p-6">
                  <div className="h-16 bg-white/5 rounded-lg" />
                </CardContent>
              </Card>
            ))}
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background" data-testid="dashboard">
      <Navbar user={user} />
      
      {/* Hero Glow */}
      <div className="hero-glow opacity-50" />

      <main className="relative z-10 max-w-7xl mx-auto px-6 py-8">
        {/* Welcome Header */}
        <div className="mb-8 animate-fade-in">
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Welcome back, {user?.name?.split(" ")[0] || "User"}
          </h1>
          <p className="text-muted-foreground">
            Here's an overview of your job search progress
          </p>
        </div>

        {/* Bento Stats Grid */}
        <BentoStats stats={stats} />

        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {quickActions.map((action, i) => (
              <Card
                key={i}
                data-testid={`quick-action-${action.label.toLowerCase().replace(/\s/g, '-')}`}
                className="glass-light card-hover cursor-pointer group"
                onClick={() => navigate(action.path)}
              >
                <CardContent className="p-6">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${action.color} flex items-center justify-center mb-4`}>
                    <action.icon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-1 flex items-center gap-2">
                    {action.label}
                    <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
                  </h3>
                  <p className="text-sm text-muted-foreground">{action.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Recent Applications */}
        <div className="grid gap-6 lg:grid-cols-2 mb-8">
          <Card className="glass-light" data-testid="recent-applications">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-indigo-500" />
                Recent Applications
              </CardTitle>
            </CardHeader>
            <CardContent>
              {stats?.recent_applications?.length > 0 ? (
                <div className="space-y-4">
                  {stats.recent_applications.map((app, i) => (
                    <div
                      key={app.application_id || i}
                      className="flex items-center justify-between p-4 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 truncate">{app.job_title}</p>
                        <p className="text-sm text-gray-500 truncate">{app.company}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <Badge className={`${getStatusColor(app.status)} capitalize`}>
                          {app.status}
                        </Badge>
                        <span className="text-sm font-bold text-emerald-600">{app.match_score}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <AlertCircle className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">No applications yet</p>
                  <Button
                    variant="link"
                    className="text-indigo-400 mt-2"
                    onClick={() => navigate("/jobs")}
                  >
                    Start searching for jobs
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Profile Completion Guide */}
          <Card className="glass-light" data-testid="profile-guide">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="w-5 h-5 text-emerald-500" />
                Complete Your Profile
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center gap-3 p-4 rounded-lg bg-gray-50">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${stats?.profile_completeness >= 40 ? 'bg-emerald-50 text-emerald-600' : 'bg-gray-100 text-gray-400'}`}>
                    {stats?.profile_completeness >= 40 ? <CheckCircle className="w-4 h-4" /> : '1'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">Upload Resume</p>
                    <p className="text-sm text-gray-500">Required for ATS optimization</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-4 rounded-lg bg-gray-50">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${stats?.profile_completeness >= 60 ? 'bg-emerald-50 text-emerald-600' : 'bg-gray-100 text-gray-400'}`}>
                    {stats?.profile_completeness >= 60 ? <CheckCircle className="w-4 h-4" /> : '2'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">Add Skills</p>
                    <p className="text-sm text-gray-500">Improve job matching accuracy</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-4 rounded-lg bg-gray-50">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${stats?.profile_completeness >= 80 ? 'bg-emerald-50 text-emerald-600' : 'bg-gray-100 text-gray-400'}`}>
                    {stats?.profile_completeness >= 80 ? <CheckCircle className="w-4 h-4" /> : '3'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">Set Preferences</p>
                    <p className="text-sm text-gray-500">Location, salary, job type</p>
                  </div>
                </div>

                <Button
                  data-testid="complete-profile-btn"
                  className="w-full bg-indigo-500 hover:bg-indigo-600 mt-4"
                  onClick={() => navigate("/profile")}
                >
                  Complete Profile
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Saved Jobs Section */}
        <Card className="glass-light" data-testid="saved-jobs">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Briefcase className="w-5 h-5 text-amber-500" />
              Your Saved Jobs
              {savedJobs?.jobs?.filter(j => j.is_new_for_user).length > 0 && (
                <Badge className="bg-amber-50 text-amber-700 border-amber-200 ml-2">
                  <Star className="w-3 h-3 mr-1 fill-amber-500" />
                  {savedJobs.jobs.filter(j => j.is_new_for_user).length} New
                </Badge>
              )}
            </CardTitle>
            <Button
              data-testid="find-new-jobs-btn"
              className="bg-indigo-500 hover:bg-indigo-600"
              onClick={() => navigate("/jobs")}
            >
              <Search className="w-4 h-4 mr-2" />
              Find New Jobs
            </Button>
          </CardHeader>
          <CardContent>
            {savedJobs?.jobs?.length > 0 ? (
              <>
                {savedJobs.last_search_query && (
                  <p className="text-sm text-muted-foreground mb-4">
                    Last search: &quot;{savedJobs.last_search_query}&quot; in {savedJobs.last_search_location || "Any location"}
                    {savedJobs.updated_at && (
                      <span className="ml-2">
                        • Updated {new Date(savedJobs.updated_at).toLocaleDateString()}
                      </span>
                    )}
                  </p>
                )}
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {savedJobs.jobs.slice(0, 6).map((job, i) => (
                    <div
                      key={job.job_id || i}
                      className={`relative p-4 rounded-lg border transition-all hover:shadow-md ${
                        job.is_new_for_user 
                          ? 'bg-amber-50/50 border-amber-200 hover:border-amber-300' 
                          : 'bg-white border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      {/* New Job Star Badge */}
                      {job.is_new_for_user && (
                        <div className="absolute -top-2 -right-2 bg-amber-500 text-white text-xs px-2 py-0.5 rounded-full flex items-center gap-1 shadow-lg">
                          <Star className="w-3 h-3 fill-white" />
                          NEW
                        </div>
                      )}
                      
                      <div className="flex items-start justify-between mb-2">
                        <h3 className="font-semibold text-foreground text-sm line-clamp-2 pr-6 cursor-pointer hover:text-indigo-500" onClick={() => job.apply_link && window.open(job.apply_link, '_blank')}>
                          {job.title}
                        </h3>
                        {job.match_score && (
                          <Badge className={`text-xs shrink-0 ${
                            job.match_score >= 70 
                              ? 'bg-emerald-50 text-emerald-700' 
                              : job.match_score >= 50 
                                ? 'bg-amber-50 text-amber-700'
                                : 'bg-gray-50 text-gray-700'
                          }`}>
                            {job.match_score}%
                          </Badge>
                        )}
                      </div>
                      
                      <div className="space-y-1 text-xs text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Building className="w-3 h-3" />
                          <span className="truncate">{job.company}</span>
                        </div>
                        {job.location && (
                          <div className="flex items-center gap-1">
                            <MapPin className="w-3 h-3" />
                            <span className="truncate">{job.location}</span>
                          </div>
                        )}
                        <div className="flex items-center gap-1">
                          <DollarSign className="w-3 h-3" />
                          {(() => {
                            const displaySalary = getDisplaySalary(job);
                            const hasSalary = displaySalary !== 'Salary not listed';
                            return (
                              <span className={`truncate ${hasSalary ? "text-emerald-600" : ""}`}>
                                {displaySalary}
                              </span>
                            );
                          })()}
                        </div>
                      </div>

                      {/* Description toggle */}
                      {(job.description || job.description_preview) ? (
                        <div className="mt-2">
                          <button
                            className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                            onClick={(e) => { e.stopPropagation(); setExpandedJobId(expandedJobId === (job.job_id || i) ? null : (job.job_id || i)); }}
                            data-testid={`expand-desc-btn-${i}`}
                          >
                            <FileText className="w-3 h-3" />
                            {expandedJobId === (job.job_id || i) ? "Hide" : "Show"} Job Description
                            {expandedJobId === (job.job_id || i) ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                          </button>
                          {expandedJobId === (job.job_id || i) && (
                            <div className="mt-2 p-3 rounded-md bg-gray-50 border border-gray-200 max-h-72 overflow-y-auto">
                              <FormattedJobDescription 
                                description={job.description || job.description_preview} 
                                className="text-xs"
                              />
                            </div>
                          )}
                        </div>
                      ) : job.apply_link ? (
                        <div className="mt-2 text-xs text-muted-foreground italic">
                          Full description not available.{" "}
                          <a 
                            href={job.apply_link} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-indigo-400 hover:text-indigo-300"
                            onClick={(e) => e.stopPropagation()}
                          >
                            View Original →
                          </a>
                        </div>
                      ) : null}
                      
                      <div className="mt-3 flex items-center justify-between">
                        <Badge 
                          variant="outline" 
                          className={`text-xs capitalize ${
                            ['greenhouse', 'lever', 'ashby'].includes(job.source?.toLowerCase())
                              ? 'bg-indigo-50 text-indigo-600 border-indigo-200'
                              : ''
                          }`}
                        >
                          {job.source}
                        </Badge>
                        <button className="text-gray-400 hover:text-indigo-500 transition-colors" onClick={() => job.apply_link && window.open(job.apply_link, '_blank')}>
                          <ExternalLink className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
                
                {savedJobs.jobs.length > 6 && (
                  <div className="mt-4 text-center">
                    <Button
                      variant="ghost"
                      className="text-indigo-400"
                      onClick={() => navigate("/jobs")}
                    >
                      View all {savedJobs.jobs.length} saved jobs
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-12">
                <Search className="w-16 h-16 text-muted-foreground mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-medium text-foreground mb-2">No saved jobs yet</h3>
                <p className="text-muted-foreground mb-4">
                  Search for jobs and they'll appear here for quick access
                </p>
                <Button
                  className="bg-indigo-500 hover:bg-indigo-600"
                  onClick={() => navigate("/jobs")}
                >
                  <Search className="w-4 h-4 mr-2" />
                  Find Jobs
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
