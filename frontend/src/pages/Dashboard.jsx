import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { API } from "@/App";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import Navbar from "@/components/Navbar";
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
} from "lucide-react";
import { toast } from "sonner";

export default function Dashboard({ user }) {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [savedJobs, setSavedJobs] = useState(null);
  const [loading, setLoading] = useState(true);

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

          <Card className="glass-light card-hover animate-fade-in-delay-2" data-testid="stat-pending">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Pending Review</p>
                  <p className="text-3xl font-bold text-foreground">{stats?.pending || 0}</p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-amber-500/20 flex items-center justify-center">
                  <Clock className="w-6 h-6 text-amber-400" />
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
        <div className="grid gap-6 lg:grid-cols-2">
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
      </main>
    </div>
  );
}
