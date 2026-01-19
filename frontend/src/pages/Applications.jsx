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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
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
  Download,
  ExternalLink,
  Eye,
  Copy,
  CheckCheck,
  Rocket,
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
  const [expandedApp, setExpandedApp] = useState(null);
  const [reviewApp, setReviewApp] = useState(null);
  const [submitApp, setSubmitApp] = useState(null);
  const [copiedField, setCopiedField] = useState(null);
  const [autoFillScript, setAutoFillScript] = useState(null);
  const [loadingScript, setLoadingScript] = useState(false);

  const copyToClipboard = async (text, field) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(field);
      toast.success("Copied to clipboard!");
      setTimeout(() => setCopiedField(null), 2000);
    } catch (err) {
      toast.error("Failed to copy");
    }
  };

  const handleOpenApplication = (app) => {
    if (app.apply_link) {
      window.open(app.apply_link, '_blank');
    } else {
      toast.error("No application link available for this job");
    }
  };

  const handleSubmitNow = async (app) => {
    setSubmitApp(app);
    setAutoFillScript(null);
    
    // Fetch the auto-fill script
    setLoadingScript(true);
    try {
      const response = await fetch(`${API}/applications/${app.application_id}/autofill-script`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setAutoFillScript(data.script);
      }
    } catch (err) {
      console.error('Failed to load auto-fill script:', err);
    } finally {
      setLoadingScript(false);
    }
  };

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

  const handleBulkApprove = async () => {
    const pendingApps = applications.filter(app => app.status === "pending");
    if (pendingApps.length === 0) return;
    
    setBulkApproveLoading(true);
    setShowBulkConfirm(false);
    
    let successCount = 0;
    let failCount = 0;
    
    for (const app of pendingApps) {
      try {
        const response = await fetch(`${API}/applications/${app.application_id}/approve`, {
          method: "PUT",
          credentials: "include",
        });
        if (response.ok) {
          successCount++;
          setApplications(apps => apps.map(a =>
            a.application_id === app.application_id
              ? { ...a, status: "applied", applied_at: new Date().toISOString() }
              : a
          ));
        } else {
          failCount++;
        }
      } catch (error) {
        failCount++;
      }
    }
    
    setBulkApproveLoading(false);
    
    if (successCount > 0 && failCount === 0) {
      toast.success(`All ${successCount} applications approved and submitted!`);
    } else if (successCount > 0 && failCount > 0) {
      toast.warning(`${successCount} approved, ${failCount} failed`);
    } else {
      toast.error("Failed to approve applications");
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
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
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
            
            {/* Bulk Apply Button */}
            {counts.pending > 0 && (
              <Button
                data-testid="bulk-approve-btn"
                onClick={() => setShowBulkConfirm(true)}
                disabled={bulkApproveLoading}
                className="bg-emerald-500 hover:bg-emerald-600"
              >
                {bulkApproveLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Approving...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4 mr-2" />
                    Approve All Pending ({counts.pending})
                  </>
                )}
              </Button>
            )}
          </div>
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
                                  <div className="flex items-center justify-between mb-2">
                                    <h5 className="text-sm font-medium text-emerald-400 flex items-center gap-2">
                                      <FileText className="w-4 h-4" />
                                      Optimized Resume
                                    </h5>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={async () => {
                                        try {
                                          const response = await fetch(`${API}/applications/${app.application_id}/download/resume`, {
                                            credentials: 'include'
                                          });
                                          if (!response.ok) throw new Error('Download failed');
                                          const blob = await response.blob();
                                          const url = window.URL.createObjectURL(blob);
                                          const a = document.createElement('a');
                                          a.href = url;
                                          a.download = `Resume_${app.company.replace(/\s+/g, '_')}_${app.job_title.replace(/\s+/g, '_')}.docx`;
                                          document.body.appendChild(a);
                                          a.click();
                                          window.URL.revokeObjectURL(url);
                                          a.remove();
                                        } catch (err) {
                                          toast.error('Failed to download resume');
                                        }
                                      }}
                                      className="h-7 text-xs border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20"
                                    >
                                      <Download className="w-3 h-3 mr-1" />
                                      Download .docx
                                    </Button>
                                  </div>
                                  <pre className="text-xs text-muted-foreground whitespace-pre-wrap font-sans max-h-60 overflow-auto">
                                    {app.optimized_resume}
                                  </pre>
                                </div>
                              )}
                              {app.cover_letter && (
                                <div className="p-4 rounded-lg bg-indigo-500/10 border border-indigo-500/20">
                                  <div className="flex items-center justify-between mb-2">
                                    <h5 className="text-sm font-medium text-indigo-400 flex items-center gap-2">
                                      <MessageSquare className="w-4 h-4" />
                                      Cover Letter
                                    </h5>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={async () => {
                                        try {
                                          const response = await fetch(`${API}/applications/${app.application_id}/download/cover-letter`, {
                                            credentials: 'include'
                                          });
                                          if (!response.ok) throw new Error('Download failed');
                                          const blob = await response.blob();
                                          const url = window.URL.createObjectURL(blob);
                                          const a = document.createElement('a');
                                          a.href = url;
                                          a.download = `Cover_Letter_${app.company.replace(/\s+/g, '_')}_${app.job_title.replace(/\s+/g, '_')}.docx`;
                                          document.body.appendChild(a);
                                          a.click();
                                          window.URL.revokeObjectURL(url);
                                          a.remove();
                                        } catch (err) {
                                          toast.error('Failed to download cover letter');
                                        }
                                      }}
                                      className="h-7 text-xs border-indigo-500/30 text-indigo-400 hover:bg-indigo-500/20"
                                    >
                                      <Download className="w-3 h-3 mr-1" />
                                      Download .docx
                                    </Button>
                                  </div>
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
                    <div className="flex flex-col gap-2">
                      {/* Primary Actions Row */}
                      <div className="flex items-center gap-2">
                        <Button
                          data-testid={`review-btn-${i}`}
                          size="sm"
                          variant="outline"
                          onClick={() => setReviewApp(app)}
                          className="border-indigo-500/30 text-indigo-400 hover:bg-indigo-500/20"
                        >
                          <Eye className="w-4 h-4 mr-1" />
                          Review
                        </Button>
                        <Button
                          data-testid={`open-app-btn-${i}`}
                          size="sm"
                          variant="outline"
                          onClick={() => handleOpenApplication(app)}
                          className="border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/20"
                        >
                          <ExternalLink className="w-4 h-4 mr-1" />
                          Open Application
                        </Button>
                      </div>
                      
                      {/* Status-based Actions Row */}
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
                                  <CheckCircle className="w-4 h-4 mr-1" />
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
                        {app.status === "applied" && (
                          <Button
                            data-testid={`submit-now-btn-${i}`}
                            size="sm"
                            onClick={() => handleSubmitNow(app)}
                            className="bg-indigo-500 hover:bg-indigo-600"
                          >
                            <Rocket className="w-4 h-4 mr-1" />
                            Submit Now
                          </Button>
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

      {/* Bulk Approve Confirmation Dialog */}
      <AlertDialog open={showBulkConfirm} onOpenChange={setShowBulkConfirm}>
        <AlertDialogContent className="bg-background border-white/10">
          <AlertDialogHeader>
            <AlertDialogTitle>Approve All Pending Applications?</AlertDialogTitle>
            <AlertDialogDescription>
              This will approve and submit all {counts.pending} pending application{counts.pending !== 1 ? 's' : ''}. 
              Each application will be marked as submitted with its optimized resume and cover letter (if generated).
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="border-white/10">Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleBulkApprove}
              className="bg-emerald-500 hover:bg-emerald-600"
            >
              <Send className="w-4 h-4 mr-2" />
              Approve All ({counts.pending})
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Review Application Dialog */}
      <Dialog open={!!reviewApp} onOpenChange={() => setReviewApp(null)}>
        <DialogContent className="bg-background border-white/10 max-w-4xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Eye className="w-5 h-5 text-indigo-400" />
              Review Application
            </DialogTitle>
            <DialogDescription>
              {reviewApp?.job_title} at {reviewApp?.company}
            </DialogDescription>
          </DialogHeader>
          
          <ScrollArea className="max-h-[70vh] pr-4">
            <div className="space-y-6">
              {/* Match Info */}
              <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                <h4 className="text-sm font-medium text-foreground mb-3 flex items-center gap-2">
                  <Briefcase className="w-4 h-4 text-indigo-400" />
                  Job Details
                </h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Company:</span>
                    <span className="ml-2 text-foreground">{reviewApp?.company}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Location:</span>
                    <span className="ml-2 text-foreground">{reviewApp?.location || "Not specified"}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Match Score:</span>
                    <span className="ml-2 text-foreground">{reviewApp?.match_score}%</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Status:</span>
                    <Badge className="ml-2 capitalize">{reviewApp?.status}</Badge>
                  </div>
                </div>
              </div>

              {/* Optimized Resume */}
              {reviewApp?.optimized_resume && (
                <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-medium text-emerald-400 flex items-center gap-2">
                      <FileText className="w-4 h-4" />
                      Tailored Resume
                    </h4>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => copyToClipboard(reviewApp.optimized_resume, 'resume')}
                        className="h-7 text-xs text-emerald-400 hover:bg-emerald-500/20"
                      >
                        {copiedField === 'resume' ? <CheckCheck className="w-3 h-3 mr-1" /> : <Copy className="w-3 h-3 mr-1" />}
                        {copiedField === 'resume' ? 'Copied!' : 'Copy'}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={async () => {
                          try {
                            const response = await fetch(`${API}/applications/${reviewApp.application_id}/download/resume`, {
                              credentials: 'include'
                            });
                            if (!response.ok) throw new Error('Download failed');
                            const blob = await response.blob();
                            const url = window.URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `Resume_${reviewApp.company.replace(/\s+/g, '_')}.docx`;
                            document.body.appendChild(a);
                            a.click();
                            window.URL.revokeObjectURL(url);
                            a.remove();
                          } catch (err) {
                            toast.error('Failed to download');
                          }
                        }}
                        className="h-7 text-xs border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20"
                      >
                        <Download className="w-3 h-3 mr-1" />
                        .docx
                      </Button>
                    </div>
                  </div>
                  <pre className="text-xs text-muted-foreground whitespace-pre-wrap font-sans max-h-48 overflow-auto bg-black/20 p-3 rounded">
                    {reviewApp.optimized_resume}
                  </pre>
                </div>
              )}

              {/* Cover Letter */}
              {reviewApp?.cover_letter && (
                <div className="p-4 rounded-lg bg-indigo-500/10 border border-indigo-500/20">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-medium text-indigo-400 flex items-center gap-2">
                      <MessageSquare className="w-4 h-4" />
                      Cover Letter
                    </h4>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => copyToClipboard(reviewApp.cover_letter, 'cover')}
                        className="h-7 text-xs text-indigo-400 hover:bg-indigo-500/20"
                      >
                        {copiedField === 'cover' ? <CheckCheck className="w-3 h-3 mr-1" /> : <Copy className="w-3 h-3 mr-1" />}
                        {copiedField === 'cover' ? 'Copied!' : 'Copy'}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={async () => {
                          try {
                            const response = await fetch(`${API}/applications/${reviewApp.application_id}/download/cover-letter`, {
                              credentials: 'include'
                            });
                            if (!response.ok) throw new Error('Download failed');
                            const blob = await response.blob();
                            const url = window.URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `Cover_Letter_${reviewApp.company.replace(/\s+/g, '_')}.docx`;
                            document.body.appendChild(a);
                            a.click();
                            window.URL.revokeObjectURL(url);
                            a.remove();
                          } catch (err) {
                            toast.error('Failed to download');
                          }
                        }}
                        className="h-7 text-xs border-indigo-500/30 text-indigo-400 hover:bg-indigo-500/20"
                      >
                        <Download className="w-3 h-3 mr-1" />
                        .docx
                      </Button>
                    </div>
                  </div>
                  <pre className="text-xs text-muted-foreground whitespace-pre-wrap font-sans max-h-48 overflow-auto bg-black/20 p-3 rounded">
                    {reviewApp.cover_letter}
                  </pre>
                </div>
              )}

              {/* No documents warning */}
              {!reviewApp?.optimized_resume && !reviewApp?.cover_letter && (
                <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20 text-center">
                  <AlertCircle className="w-8 h-8 text-amber-400 mx-auto mb-2" />
                  <p className="text-sm text-amber-400">No tailored documents generated yet.</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Go to Job Search to generate an optimized resume and cover letter for this position.
                  </p>
                </div>
              )}
            </div>
          </ScrollArea>

          <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
            <Button variant="outline" onClick={() => setReviewApp(null)} className="border-white/10">
              Close
            </Button>
            <Button 
              onClick={() => handleOpenApplication(reviewApp)}
              className="bg-cyan-500 hover:bg-cyan-600"
            >
              <ExternalLink className="w-4 h-4 mr-2" />
              Open Application
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Submit Now Dialog - Assisted Apply */}
      <Dialog open={!!submitApp} onOpenChange={() => { setSubmitApp(null); setAutoFillScript(null); }}>
        <DialogContent className="bg-background border-white/10 max-w-2xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Rocket className="w-5 h-5 text-indigo-400" />
              Submit Application
            </DialogTitle>
            <DialogDescription>
              {submitApp?.job_title} at {submitApp?.company}
            </DialogDescription>
          </DialogHeader>
          
          <ScrollArea className="max-h-[65vh]">
            <div className="space-y-4 pr-4">
              {/* Auto-Fill Script Section */}
              <div className="p-4 rounded-lg bg-gradient-to-r from-indigo-500/20 to-purple-500/20 border border-indigo-500/30">
                <h4 className="text-sm font-medium text-indigo-400 mb-2 flex items-center gap-2">
                  <Rocket className="w-4 h-4" />
                  Auto-Fill (Recommended)
                </h4>
                <p className="text-sm text-muted-foreground mb-3">
                  Copy our auto-fill script and paste it in the browser console on the application page. 
                  It will automatically fill in your name, email, resume, and cover letter.
                </p>
                {loadingScript ? (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className="text-sm">Generating auto-fill script...</span>
                  </div>
                ) : autoFillScript ? (
                  <div className="space-y-2">
                    <Button
                      onClick={() => copyToClipboard(autoFillScript, 'autofill-script')}
                      className={`w-full ${copiedField === 'autofill-script' ? 'bg-emerald-500 hover:bg-emerald-600' : 'bg-indigo-500 hover:bg-indigo-600'}`}
                    >
                      {copiedField === 'autofill-script' ? (
                        <>
                          <CheckCheck className="w-4 h-4 mr-2" />
                          Script Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="w-4 h-4 mr-2" />
                          Copy Auto-Fill Script
                        </>
                      )}
                    </Button>
                    <p className="text-xs text-muted-foreground">
                      After copying: Open app page → Press F12 → Go to Console tab → Paste → Press Enter
                    </p>
                  </div>
                ) : (
                  <p className="text-xs text-amber-400">Could not generate auto-fill script</p>
                )}
              </div>

              {/* Manual Option */}
              <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                <h4 className="text-sm font-medium text-foreground mb-3">Or Copy Manually:</h4>
                <div className="grid grid-cols-2 gap-3">
                  {submitApp?.optimized_resume && (
                    <Button
                      variant="outline"
                      onClick={() => copyToClipboard(submitApp.optimized_resume, 'submit-resume')}
                      className="h-auto py-3 flex-col items-center gap-2 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20"
                    >
                      {copiedField === 'submit-resume' ? <CheckCheck className="w-5 h-5" /> : <FileText className="w-5 h-5" />}
                      <span className="text-xs">{copiedField === 'submit-resume' ? 'Resume Copied!' : 'Copy Resume'}</span>
                    </Button>
                  )}
                  {submitApp?.cover_letter && (
                    <Button
                      variant="outline"
                      onClick={() => copyToClipboard(submitApp.cover_letter, 'submit-cover')}
                      className="h-auto py-3 flex-col items-center gap-2 border-indigo-500/30 text-indigo-400 hover:bg-indigo-500/20"
                    >
                      {copiedField === 'submit-cover' ? <CheckCheck className="w-5 h-5" /> : <MessageSquare className="w-5 h-5" />}
                      <span className="text-xs">{copiedField === 'submit-cover' ? 'Cover Letter Copied!' : 'Copy Cover Letter'}</span>
                    </Button>
                  )}
                </div>
              </div>

              {/* Instructions */}
              <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                <h4 className="text-sm font-medium text-foreground mb-2">How to Use Auto-Fill:</h4>
                <ol className="text-sm text-muted-foreground space-y-1 list-decimal list-inside">
                  <li>Click &quot;Copy Auto-Fill Script&quot; above</li>
                  <li>Click &quot;Open Application Page&quot; below</li>
                  <li>On the job site, press <kbd className="px-1.5 py-0.5 bg-white/10 rounded text-xs">F12</kbd> to open Developer Tools</li>
                  <li>Click the &quot;Console&quot; tab</li>
                  <li>Paste the script (Ctrl+V) and press Enter</li>
                  <li>Review the filled fields, upload resume if needed</li>
                  <li>Complete any CAPTCHA and submit</li>
                </ol>
              </div>

              {!submitApp?.optimized_resume && !submitApp?.cover_letter && (
                <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                  <p className="text-sm text-amber-400 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4" />
                    No tailored documents. You can still apply with your original resume.
                  </p>
                </div>
              )}
            </div>
          </ScrollArea>

          <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
            <Button variant="outline" onClick={() => setSubmitApp(null)} className="border-white/10">
              Cancel
            </Button>
            <Button 
              onClick={() => {
                handleOpenApplication(submitApp);
                toast.success("Application page opened. Good luck!");
              }}
              className="bg-indigo-500 hover:bg-indigo-600"
            >
              <ExternalLink className="w-4 h-4 mr-2" />
              Open Application Page
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
