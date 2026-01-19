import { useState, useEffect } from "react";
import { API } from "@/App";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import Navbar from "@/components/Navbar";
import {
  Briefcase,
  CheckCircle,
  Clock,
  XCircle,
  Trash2,
  Send,
  Building,
  MapPin,
  Loader2,
  AlertCircle,
  FileText,
  MessageSquare,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { toast } from "sonner";

export default function Applications({ user }) {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("all");
  const [deleteId, setDeleteId] = useState(null);
  const [actionLoading, setActionLoading] = useState(null);
  const [bulkApproveLoading, setBulkApproveLoading] = useState(false);
  const [showBulkConfirm, setShowBulkConfirm] = useState(false);

  useEffect(() => {
    fetchApplications();
  }, []);

  const fetchApplications = async () => {
    try {
      const response = await fetch(`${API}/applications`, {
        credentials: "include",
      });
      if (!response.ok) throw new Error("Failed to fetch applications");
      const data = await response.json();
      setApplications(data.applications || []);
    } catch (error) {
      toast.error("Failed to load applications");
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (applicationId) => {
    setActionLoading(applicationId);
    try {
      const response = await fetch(`${API}/applications/${applicationId}/approve`, {
        method: "PUT",
        credentials: "include",
      });
      if (!response.ok) throw new Error("Failed to approve application");
      
      setApplications(apps => apps.map(app =>
        app.application_id === applicationId
          ? { ...app, status: "applied", applied_at: new Date().toISOString() }
          : app
      ));
      toast.success("Application approved and submitted!");
    } catch (error) {
      toast.error("Failed to approve application");
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (applicationId) => {
    setActionLoading(applicationId);
    try {
      const response = await fetch(`${API}/applications/${applicationId}/reject`, {
        method: "PUT",
        credentials: "include",
      });
      if (!response.ok) throw new Error("Failed to reject application");
      
      setApplications(apps => apps.map(app =>
        app.application_id === applicationId
          ? { ...app, status: "rejected" }
          : app
      ));
      toast.info("Application skipped");
    } catch (error) {
      toast.error("Failed to skip application");
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    setActionLoading(deleteId);
    try {
      const response = await fetch(`${API}/applications/${deleteId}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!response.ok) throw new Error("Failed to delete application");
      
      setApplications(apps => apps.filter(app => app.application_id !== deleteId));
      toast.success("Application deleted");
    } catch (error) {
      toast.error("Failed to delete application");
    } finally {
      setActionLoading(null);
      setDeleteId(null);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "applied":
        return <CheckCircle className="w-5 h-5 text-emerald-400" />;
      case "pending":
        return <Clock className="w-5 h-5 text-amber-400" />;
      case "rejected":
        return <XCircle className="w-5 h-5 text-red-400" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
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

  const getMatchScoreClass = (score) => {
    if (score >= 80) return "match-score-high";
    if (score >= 60) return "match-score-medium";
    return "match-score-low";
  };

  const filteredApps = applications.filter(app => {
    if (activeTab === "all") return true;
    return app.status === activeTab;
  });

  const counts = {
    all: applications.length,
    pending: applications.filter(a => a.status === "pending").length,
    applied: applications.filter(a => a.status === "applied").length,
    rejected: applications.filter(a => a.status === "rejected").length,
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar user={user} />
        <main className="max-w-5xl mx-auto px-6 py-8">
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="glass-light animate-pulse">
                <CardContent className="p-6">
                  <div className="h-24 bg-white/5 rounded-lg" />
                </CardContent>
              </Card>
            ))}
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background" data-testid="applications-page">
      <Navbar user={user} />
      
      <div className="hero-glow opacity-30" />

      <main className="relative z-10 max-w-5xl mx-auto px-6 py-8">
        <div className="mb-8 animate-fade-in">
          <h1 className="text-3xl font-bold text-foreground mb-2">My Applications</h1>
          <p className="text-muted-foreground">
            Track and manage your job applications
          </p>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
          <TabsList className="bg-white/5 border border-white/10">
            <TabsTrigger value="all" className="data-[state=active]:bg-indigo-500">
              All ({counts.all})
            </TabsTrigger>
            <TabsTrigger value="pending" className="data-[state=active]:bg-amber-500">
              Pending ({counts.pending})
            </TabsTrigger>
            <TabsTrigger value="applied" className="data-[state=active]:bg-emerald-500">
              Applied ({counts.applied})
            </TabsTrigger>
            <TabsTrigger value="rejected" className="data-[state=active]:bg-red-500">
              Skipped ({counts.rejected})
            </TabsTrigger>
          </TabsList>
        </Tabs>

        {/* Applications List */}
        {filteredApps.length > 0 ? (
          <div className="space-y-4" data-testid="applications-list">
            {filteredApps.map((app, i) => (
              <Card
                key={app.application_id || i}
                data-testid={`application-card-${i}`}
                className="glass-light"
              >
                <CardContent className="p-6">
                  <div className="flex flex-col md:flex-row md:items-center gap-4">
                    {/* Status Icon */}
                    <div className="hidden md:flex w-12 h-12 rounded-xl bg-white/5 items-center justify-center flex-shrink-0">
                      {getStatusIcon(app.status)}
                    </div>

                    {/* Job Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-4 mb-2">
                        <div>
                          <h3 className="text-lg font-semibold text-foreground">{app.job_title}</h3>
                          <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                            <span className="flex items-center gap-1">
                              <Building className="w-4 h-4" />
                              {app.company}
                            </span>
                            {app.location && (
                              <span className="flex items-center gap-1">
                                <MapPin className="w-4 h-4" />
                                {app.location}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge className={`${getMatchScoreClass(app.match_score)} px-3 py-1`}>
                            {app.match_score}%
                          </Badge>
                          <Badge className={`${getStatusColor(app.status)} capitalize`}>
                            {app.status}
                          </Badge>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Clock className="w-3 h-3" />
                        <span>
                          Created: {new Date(app.created_at).toLocaleDateString()}
                        </span>
                        {app.applied_at && (
                          <>
                            <span>•</span>
                            <span>Applied: {new Date(app.applied_at).toLocaleDateString()}</span>
                          </>
                        )}
                        {/* Document indicators */}
                        {(app.optimized_resume || app.cover_letter) && (
                          <>
                            <span>•</span>
                            <div className="flex items-center gap-2">
                              {app.optimized_resume && (
                                <span className="flex items-center gap-1 text-emerald-400">
                                  <FileText className="w-3 h-3" />
                                  Resume
                                </span>
                              )}
                              {app.cover_letter && (
                                <span className="flex items-center gap-1 text-indigo-400">
                                  <MessageSquare className="w-3 h-3" />
                                  Cover Letter
                                </span>
                              )}
                            </div>
                          </>
                        )}
                      </div>

                      {/* Expandable Documents Section */}
                      {(app.optimized_resume || app.cover_letter) && (
                        <div className="mt-3">
                          <button
                            onClick={() => setExpandedApp(expandedApp === app.application_id ? null : app.application_id)}
                            className="flex items-center gap-1 text-sm text-indigo-400 hover:text-indigo-300 transition-colors"
                          >
                            {expandedApp === app.application_id ? (
                              <ChevronUp className="w-4 h-4" />
                            ) : (
                              <ChevronDown className="w-4 h-4" />
                            )}
                            {expandedApp === app.application_id ? "Hide" : "View"} saved documents
                          </button>
                          
                          {expandedApp === app.application_id && (
                            <div className="mt-4 space-y-4">
                              {app.optimized_resume && (
                                <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                                  <h5 className="text-sm font-medium text-emerald-400 mb-2 flex items-center gap-2">
                                    <FileText className="w-4 h-4" />
                                    Optimized Resume
                                  </h5>
                                  <pre className="text-xs text-muted-foreground whitespace-pre-wrap font-sans max-h-60 overflow-auto">
                                    {app.optimized_resume}
                                  </pre>
                                </div>
                              )}
                              {app.cover_letter && (
                                <div className="p-4 rounded-lg bg-indigo-500/10 border border-indigo-500/20">
                                  <h5 className="text-sm font-medium text-indigo-400 mb-2 flex items-center gap-2">
                                    <MessageSquare className="w-4 h-4" />
                                    Cover Letter
                                  </h5>
                                  <pre className="text-xs text-muted-foreground whitespace-pre-wrap font-sans max-h-60 overflow-auto">
                                    {app.cover_letter}
                                  </pre>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2">
                      {app.status === "pending" && (
                        <>
                          <Button
                            data-testid={`approve-btn-${i}`}
                            size="sm"
                            onClick={() => handleApprove(app.application_id)}
                            disabled={actionLoading === app.application_id}
                            className="bg-emerald-500 hover:bg-emerald-600"
                          >
                            {actionLoading === app.application_id ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <>
                                <Send className="w-4 h-4 mr-1" />
                                Approve
                              </>
                            )}
                          </Button>
                          <Button
                            data-testid={`reject-btn-${i}`}
                            size="sm"
                            variant="outline"
                            onClick={() => handleReject(app.application_id)}
                            disabled={actionLoading === app.application_id}
                            className="border-white/10"
                          >
                            Skip
                          </Button>
                        </>
                      )}
                      <Button
                        data-testid={`delete-btn-${i}`}
                        size="sm"
                        variant="ghost"
                        onClick={() => setDeleteId(app.application_id)}
                        className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="text-center py-16" data-testid="empty-state">
            <AlertCircle className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-foreground mb-2">
              {activeTab === "all" ? "No Applications Yet" : `No ${activeTab} Applications`}
            </h3>
            <p className="text-muted-foreground max-w-md mx-auto">
              {activeTab === "all"
                ? "Start searching for jobs and apply to opportunities that match your profile."
                : `You don't have any ${activeTab} applications at the moment.`}
            </p>
          </div>
        )}
      </main>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <AlertDialogContent className="bg-background border-white/10">
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Application?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. The application will be permanently removed.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="border-white/10">Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-red-500 hover:bg-red-600"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
