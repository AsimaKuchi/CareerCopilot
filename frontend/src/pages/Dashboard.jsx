import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { API } from "@/App";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import Navbar from "@/components/Navbar";
import FormattedJobDescription from "@/components/FormattedJobDescription";
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
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "pending":
        return "bg-amber-500/10 text-amber-400 border-amber-500/20";
      case "rejected":
        return "bg-red-500/10 text-red-400 border-red-500/20";
      default:
        return "bg-gray-500/10 text-gray-400 border-gray-500/20";
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

        {/* Stats Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
          <Card className="glass-light card-hover animate-fade-in" data-testid="stat-total">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Total Applications</p>
                  <p className="text-3xl font-bold text-foreground">{stats?.total_applications || 0}</p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-indigo-500/20 flex items-center justify-center">
                  <Briefcase className="w-6 h-6 text-indigo-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="glass-light card-hover animate-fade-in-delay-1" data-testid="stat-applied">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Applied</p>
                  <p className="text-3xl font-bold text-foreground">{stats?.applied || 0}</p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center">
                  <CheckCircle className="w-6 h-6 text-emerald-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="glass-light card-hover animate-fade-in-delay-2" data-testid="stat-time-saved">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Time Saved</p>
                  <p className="text-3xl font-bold text-foreground">
                    {(stats?.time_saved?.total_minutes || 0) >= 60
                      ? `${stats?.time_saved?.total_hours || 0}h`
                      : `${stats?.time_saved?.total_minutes || 0}m`}
                  </p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-amber-500/20 flex items-center justify-center">
                  <Timer className="w-6 h-6 text-amber-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="glass-light card-hover animate-fade-in-delay-3" data-testid="stat-profile">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Profile Complete</p>
                  <p className="text-3xl font-bold text-foreground">{stats?.profile_completeness || 0}%</p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-rose-500/20 flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-rose-400" />
                </div>
              </div>
              <Progress value={stats?.profile_completeness || 0} className="mt-4 h-2" />
            </CardContent>
          </Card>
        </div>

        {/* Time Saved Breakdown */}
        {(stats?.time_saved?.total_minutes || 0) > 0 && (
          <Card className="glass-light mb-8 animate-fade-in" data-testid="time-saved-breakdown">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Zap className="w-5 h-5 text-amber-400" />
                Time Saved Breakdown
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-3">
                <div className="flex items-center gap-3 p-3 rounded-lg bg-indigo-500/5">
                  <Briefcase className="w-5 h-5 text-indigo-400 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {stats.time_saved.breakdown?.autofill_min || 0} min
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {stats.time_saved.applications_autofilled || 0} applications auto-filled
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-emerald-500/5">
                  <FileText className="w-5 h-5 text-emerald-400 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {stats.time_saved.breakdown?.resume_min || 0} min
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {stats.time_saved.resumes_generated || 0} resumes optimized
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-rose-500/5">
                  <Sparkles className="w-5 h-5 text-rose-400 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {stats.time_saved.breakdown?.cover_letter_min || 0} min
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {stats.time_saved.cover_letters_generated || 0} cover letters generated
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-foreground mb-4">Quick Actions</h2>
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
                  <h3 className="text-lg font-semibold text-foreground mb-1 flex items-center gap-2">
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
                <Briefcase className="w-5 h-5 text-indigo-400" />
                Recent Applications
              </CardTitle>
            </CardHeader>
            <CardContent>
              {stats?.recent_applications?.length > 0 ? (
                <div className="space-y-4">
                  {stats.recent_applications.map((app, i) => (
                    <div
                      key={app.application_id || i}
                      className="flex items-center justify-between p-4 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-foreground truncate">{app.job_title}</p>
                        <p className="text-sm text-muted-foreground truncate">{app.company}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <Badge className={`${getStatusColor(app.status)} capitalize`}>
                          {app.status}
                        </Badge>
                        <span className="text-sm font-bold text-emerald-400">{app.match_score}%</span>
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
                <Target className="w-5 h-5 text-emerald-400" />
                Complete Your Profile
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center gap-3 p-4 rounded-lg bg-white/5">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${stats?.profile_completeness >= 40 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-gray-500/20 text-gray-400'}`}>
                    {stats?.profile_completeness >= 40 ? <CheckCircle className="w-4 h-4" /> : '1'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-foreground">Upload Resume</p>
                    <p className="text-sm text-muted-foreground">Required for ATS optimization</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-4 rounded-lg bg-white/5">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${stats?.profile_completeness >= 60 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-gray-500/20 text-gray-400'}`}>
                    {stats?.profile_completeness >= 60 ? <CheckCircle className="w-4 h-4" /> : '2'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-foreground">Add Skills</p>
                    <p className="text-sm text-muted-foreground">Improve job matching accuracy</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-4 rounded-lg bg-white/5">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${stats?.profile_completeness >= 80 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-gray-500/20 text-gray-400'}`}>
                    {stats?.profile_completeness >= 80 ? <CheckCircle className="w-4 h-4" /> : '3'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-foreground">Set Preferences</p>
                    <p className="text-sm text-muted-foreground">Location, salary, job type</p>
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
              <Briefcase className="w-5 h-5 text-amber-400" />
              Your Saved Jobs
              {savedJobs?.jobs?.filter(j => j.is_new_for_user).length > 0 && (
                <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30 ml-2">
                  <Star className="w-3 h-3 mr-1 fill-amber-400" />
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
                      className={`relative p-4 rounded-lg border transition-all hover:shadow-lg ${
                        job.is_new_for_user 
                          ? 'bg-amber-500/5 border-amber-500/30 hover:border-amber-500/50' 
                          : 'bg-white/5 border-white/10 hover:border-white/20'
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
                              ? 'bg-emerald-500/20 text-emerald-400' 
                              : job.match_score >= 50 
                                ? 'bg-amber-500/20 text-amber-400'
                                : 'bg-gray-500/20 text-gray-400'
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
                          <span className={`truncate ${(job.job_min_salary || job.job_max_salary || job.salary_min || job.salary_max) ? "text-emerald-400" : ""}`}>
                            {job.job_min_salary || job.salary_min
                              ? `$${(job.job_min_salary || job.salary_min).toLocaleString()}${(job.job_max_salary || job.salary_max) ? ` - $${(job.job_max_salary || job.salary_max).toLocaleString()}` : '+'}`
                              : "Salary not listed"}
                          </span>
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
                            <div className="mt-2 p-3 rounded-md bg-black/20 border border-white/5 max-h-72 overflow-y-auto">
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
                              ? 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30'
                              : ''
                          }`}
                        >
                          {job.source}
                        </Badge>
                        <button className="text-muted-foreground hover:text-indigo-400 transition-colors" onClick={() => job.apply_link && window.open(job.apply_link, '_blank')}>
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
