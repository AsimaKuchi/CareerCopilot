import { useState, useEffect } from "react";
import { API } from "@/App";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
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
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import Navbar from "@/components/Navbar";
import NextStepsCard from "@/components/NextStepsCard";
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
  Lightbulb,
  DollarSign,
  Info,
  GraduationCap,
  Wand2,
} from "lucide-react";
import { toast } from "sonner";

const forceDownload = (url) => {
  const a = document.createElement("a");
  a.href = url;
  a.download = "";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
};


export default function Applications({ user }) {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("all");
  const [deleteId, setDeleteId] = useState(null);
  const [actionLoading, setActionLoading] = useState(null);
  const [bulkApproveLoading, setBulkApproveLoading] = useState(false);
  const [showBulkConfirm, setShowBulkConfirm] = useState(false);
  const [expandedApp, setExpandedApp] = useState(null);
  const [expandedJobDetails, setExpandedJobDetails] = useState(null); // For job description expansion
  const [reviewApp, setReviewApp] = useState(null);
  const [submitApp, setSubmitApp] = useState(null);
  const [copiedField, setCopiedField] = useState(null);
  const [autoFillScript, setAutoFillScript] = useState(null);
  const [loadingScript, setLoadingScript] = useState(false);
  const [viewDocument, setViewDocument] = useState(null); // {type: 'resume'|'cover', content: string, company: string}
  const [autoFillData, setAutoFillData] = useState(null); // Auto-fill data modal
  const [confirmSubmit, setConfirmSubmit] = useState(null); // Confirmation modal for auto-submit {applicationId, company, jobTitle, applyLink}
  const [previewData, setPreviewData] = useState(null); // Preview data for confirmation modal
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [showInterviewPrep, setShowInterviewPrep] = useState(false);
  const [interviewPrepApp, setInterviewPrepApp] = useState(null);
  const [interviewPrepLoading, setInterviewPrepLoading] = useState(false);
  const [interviewPrepMaterials, setInterviewPrepMaterials] = useState("");

  // Interview Prep Handler
  const handleInterviewPrep = async (app) => {
    setInterviewPrepApp(app);
    setInterviewPrepMaterials("");
    setShowInterviewPrep(true);
    setInterviewPrepLoading(true);

    try {
      const response = await fetch(`${API}/ai/interview-prep`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          job_title: app.job_title,
          company: app.company,
          job_description: app.job_description || `${app.job_title} position at ${app.company}`,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to generate prep materials");
      }

      const data = await response.json();
      setInterviewPrepMaterials(data.prep_materials);
      toast.success("Interview prep materials ready!");
    } catch (error) {
      toast.error(error.message || "Failed to generate prep materials");
      setInterviewPrepMaterials("");
    } finally {
      setInterviewPrepLoading(false);
    }
  };

  // Fetch preview data when user clicks Auto-Apply
  const handleAutoApplyClick = async (applicationId, jobTitle, company, applyLink) => {
    setLoadingPreview(true);
    setConfirmSubmit({ applicationId, jobTitle, company, applyLink });
    
    try {
      const response = await fetch(`${API}/applications/${applicationId}/autofill-payload`, {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        setPreviewData(data);
      }
    } catch (err) {
      console.error("Failed to load preview data:", err);
    } finally {
      setLoadingPreview(false);
    }
  };

  // Copy entire document to clipboard
  const copyDocument = async () => {
    if (viewDocument?.content) {
      try {
        await navigator.clipboard.writeText(viewDocument.content);
        toast.success("Copied to clipboard! You can now paste into Word or Google Docs.");
      } catch (err) {
        toast.error("Failed to copy");
      }
    }
  };

  // Download document as .docx with formatting preserved
  const downloadDocument = async (text, companyName, type = 'resume') => {
    if (!text) {
      toast.error("No content to download");
      return;
    }
    
    try {
      const response = await fetch(`${API}/ai/download-docx`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          content: text,
          doc_type: type === 'cover' ? 'cover_letter' : 'resume',
          job_title: "",
          company: companyName || "",
        }),
      });
      
      if (!response.ok) throw new Error("Download failed");
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const safeName = (companyName || "Document").replace(/[^a-zA-Z0-9]/g, "_").slice(0, 30);
      a.download = type === 'cover'
        ? `Cover_Letter_${safeName}.docx`
        : `Resume_${safeName}.docx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      toast.success(`${type === 'cover' ? 'Cover letter' : 'Resume'} downloaded!`);
    } catch (err) {
      console.error('Download error:', err);
      toast.error(`Download failed: ${err.message}`);
    }
  };

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
      window.open(app.apply_link, "_blank");
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
      const response = await fetch(
        `${API}/applications/${app.application_id}/autofill-script`,
        {
          credentials: "include",
        }
      );
      if (response.ok) {
        const data = await response.json();
        setAutoFillScript(data.script);
      }
    } catch (err) {
      console.error("Failed to load auto-fill script:", err);
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

      setApplications((apps) =>
        apps.map((app) =>
          app.application_id === applicationId
            ? { ...app, status: "applied", applied_at: new Date().toISOString() }
            : app
        )
      );
      toast.success("Application approved! You can now submit it manually.");
    } catch (error) {
      toast.error("Failed to approve application");
    } finally {
      setActionLoading(null);
    }
  };

  const handleAutoSubmit = async (applicationId, jobTitle, company) => {
    setActionLoading(applicationId);
    try {
      const response = await fetch(`${API}/applications/${applicationId}/auto-submit`, {
        method: "POST",
        credentials: "include",
      });

      const data = await response.json();

      if (data.success) {
        setApplications((apps) =>
          apps.map((app) =>
            app.application_id === applicationId
              ? {
                  ...app,
                  status: "applied",
                  applied_at: new Date().toISOString(),
                  auto_submitted: true,
                }
              : app
          )
        );
        toast.success(`✅ Auto-submitted to ${company}!`);
      } else {
        toast.error(
          <div>
            <div className="font-semibold">{data.message}</div>
            {data.fallback_link && (
              <div className="mt-2">
                <a
                  href={data.fallback_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-indigo-400 underline"
                >
                  Click here to apply manually
                </a>
              </div>
            )}
          </div>,
          { duration: 8000 }
        );

        if (response.status === 429) {
          toast.warning("Rate limit: Please wait 5 minutes between auto-submissions");
        }
      }
    } catch (error) {
      toast.error("Failed to auto-submit application");
    } finally {
      setActionLoading(null);
    }
  };

  const handleAutoFill = async (applicationId, jobTitle, company, applyLink) => {
    setActionLoading(applicationId);
    try {
      toast.info(`🔄 Auto-filling application for ${company}...`, { duration: 5000 });

      const response = await fetch(`${API}/applications/${applicationId}/auto-fill`, {
        method: "POST",
        credentials: "include",
      });

      const data = await response.json();

      if (data.success) {
        // Playwright successfully filled the form
        toast.success(
          <div>
            <div className="font-semibold">✅ {data.fields_filled?.length || 0} fields auto-filled!</div>
            <div className="text-sm mt-1">
              {data.fields_failed?.length > 0 && (
                <span className="text-amber-300">{data.fields_failed.length} fields need manual entry</span>
              )}
            </div>
          </div>,
          { duration: 5000 }
        );
        
        // Show the data modal for copying remaining fields
        setAutoFillData({
          company,
          jobTitle,
          applyLink: data.apply_link || applyLink,
          data: data.auto_fill_data,
          fieldsFilled: data.fields_filled || [],
          fieldsFailed: data.fields_failed || [],
          playwrightSuccess: true,
          manualMode: false,
          captchaDetected: false,
          message: data.message,
        });
      } else {
        // Check if CAPTCHA was detected
        if (data.captcha_detected) {
          toast.warning(
            <div>
              <div className="font-semibold">🔒 CAPTCHA Detected</div>
              <div className="text-sm mt-1">Open the application to complete it manually</div>
            </div>,
            { duration: 6000 }
          );
        } else {
          toast.info(
            <div>
              <div className="font-semibold">📋 {data.message}</div>
              <div className="text-sm mt-1">Use the copy buttons to fill the form</div>
            </div>,
            { duration: 5000 }
          );
        }
        
        // Show manual copy modal
        setAutoFillData({
          company,
          jobTitle,
          applyLink: data.apply_link || applyLink,
          data: data.auto_fill_data,
          fieldsFilled: data.fields_filled || [],
          fieldsFailed: data.fields_failed || [],
          playwrightSuccess: false,
          manualMode: true,
          captchaDetected: data.captcha_detected || false,
          message: data.message,
          hint: data.hint,
        });
      }
    } catch (error) {
      console.error("Auto-fill error:", error);
      toast.error("Failed to auto-fill application");
    } finally {
      setActionLoading(null);
    }
  };

  // Handler for auto-fill AND auto-submit (with confirmation)
  const handleAutoFillAndSubmit = async (applicationId, jobTitle, company, applyLink) => {
    setActionLoading(applicationId);
    setConfirmSubmit(null); // Close the confirmation modal
    
    try {
      toast.info(`🚀 Auto-filling and submitting application to ${company}...`, { duration: 8000 });

      const response = await fetch(`${API}/applications/${applicationId}/auto-fill`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ submit_form: true }),
      });

      const data = await response.json();

      if (data.submitted) {
        // Submit button was clicked - but check if it was confirmed
        const isConfirmed = data.submission_confirmed;
        
        if (isConfirmed) {
          toast.success(
            <div>
              <div className="font-semibold">🎉 Application Likely Submitted!</div>
              <div className="text-sm mt-1">
                {data.fields_filled?.length || 0} fields filled. Check your email for confirmation from {company}.
              </div>
            </div>,
            { duration: 10000 }
          );
        } else {
          toast.warning(
            <div>
              <div className="font-semibold">⚠️ Submit Clicked - Verify via Email</div>
              <div className="text-sm mt-1">
                Form submitted but confirmation page not detected. Please check your email.
              </div>
            </div>,
            { duration: 10000 }
          );
        }
        
        // Update the local application state
        setApplications((apps) =>
          apps.map((app) =>
            app.application_id === applicationId
              ? { ...app, status: "applied", applied_at: new Date().toISOString(), auto_submitted: true }
              : app
          )
        );
        
        // Show the data modal with submission details and screenshot
        setAutoFillData({
          company,
          jobTitle,
          applyLink: data.apply_link || applyLink,
          data: data.auto_fill_data,
          fieldsFilled: data.fields_filled || [],
          fieldsFailed: data.fields_failed || [],
          playwrightSuccess: true,
          manualMode: false,
          captchaDetected: false,
          message: isConfirmed 
            ? `✅ Submit clicked and confirmation detected! Check email for final confirmation.`
            : `⚠️ Submit clicked but confirmation not detected. Please verify via email.`,
          submitted: true,
          submissionConfirmed: isConfirmed,
          finalUrl: data.final_url,
          screenshot: data.screenshot,
        });
      } else if (data.success) {
        // Filled but not submitted (maybe submit button not found)
        toast.warning(
          <div>
            <div className="font-semibold">📝 Form Filled - Submit Manually</div>
            <div className="text-sm mt-1">
              {data.fields_filled?.length || 0} fields filled. {data.submit_error || "Please click submit manually."}
            </div>
          </div>,
          { duration: 8000 }
        );
        
        // Show the data modal
        setAutoFillData({
          company,
          jobTitle,
          applyLink: data.apply_link || applyLink,
          data: data.auto_fill_data,
          fieldsFilled: data.fields_filled || [],
          fieldsFailed: data.fields_failed || [],
          playwrightSuccess: true,
          manualMode: true,
          captchaDetected: false,
          message: data.submit_error || "Form filled - click submit on the application page",
        });
      } else {
        // Failed
        if (data.captcha_detected) {
          toast.warning(
            <div>
              <div className="font-semibold">🔒 CAPTCHA Detected</div>
              <div className="text-sm mt-1">Please complete the application manually</div>
            </div>,
            { duration: 6000 }
          );
        } else {
          toast.error(data.message || "Auto-submit failed. Please apply manually.");
        }
        
        // Show manual copy modal
        setAutoFillData({
          company,
          jobTitle,
          applyLink: data.apply_link || applyLink,
          data: data.auto_fill_data,
          fieldsFilled: data.fields_filled || [],
          fieldsFailed: data.fields_failed || [],
          playwrightSuccess: false,
          manualMode: true,
          captchaDetected: data.captcha_detected || false,
          message: data.message,
        });
      }
    } catch (error) {
      console.error("Auto-submit error:", error);
      toast.error("Failed to auto-submit application");
    } finally {
      setActionLoading(null);
    }
  };

  const isAutoFillSupported = (applyLink) => {
    if (!applyLink) return false;
    const link = applyLink.toLowerCase();
    return (
      link.includes("greenhouse.io") ||
      link.includes("lever.co") ||
      link.includes("jobs.lever") ||
      link.includes("ashbyhq.com")
    );
  };

  const handleReject = async (applicationId) => {
    setActionLoading(applicationId);
    try {
      const response = await fetch(`${API}/applications/${applicationId}/reject`, {
        method: "PUT",
        credentials: "include",
      });
      if (!response.ok) throw new Error("Failed to reject application");

      setApplications((apps) =>
        apps.map((app) =>
          app.application_id === applicationId ? { ...app, status: "rejected" } : app
        )
      );
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

      setApplications((apps) => apps.filter((app) => app.application_id !== deleteId));
      toast.success("Application deleted");
    } catch (error) {
      toast.error("Failed to delete application");
    } finally {
      setActionLoading(null);
      setDeleteId(null);
    }
  };

  const handleBulkApprove = async () => {
    const pendingApps = applications.filter((app) => app.status === "pending");
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
          setApplications((apps) =>
            apps.map((a) =>
              a.application_id === app.application_id
                ? { ...a, status: "applied", applied_at: new Date().toISOString() }
                : a
            )
          );
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
      case "approved":
        return <CheckCircle className="w-5 h-5 text-blue-400" />;
      case "ready_to_submit":
        return <Rocket className="w-5 h-5 text-purple-400" />;
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
      case "approved":
        return "bg-blue-500/10 text-blue-400 border-blue-500/20";
      case "ready_to_submit":
        return "bg-purple-500/10 text-purple-400 border-purple-500/20";
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

  const filteredApps = applications.filter((app) => {
    if (activeTab === "all") return true;
    return app.status === activeTab;
  });

  const counts = {
    all: applications.length,
    pending: applications.filter((a) => a.status === "pending").length,
    applied: applications.filter((a) => a.status === "applied").length,
    rejected: applications.filter((a) => a.status === "rejected").length,
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
          <p className="text-muted-foreground">Track and manage your job applications</p>
        </div>

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
                    <div className="hidden md:flex w-12 h-12 rounded-xl bg-white/5 items-center justify-center flex-shrink-0">
                      {getStatusIcon(app.status)}
                    </div>

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
                            <span className="flex items-center gap-1">
                              <DollarSign className="w-4 h-4" />
                              <span className={app.salary_range && app.salary_range !== "Salary not listed" ? "text-emerald-400" : "text-muted-foreground"}>
                                {app.salary_range || "Salary not listed"}
                              </span>
                            </span>
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
                        <span>Created: {new Date(app.created_at).toLocaleDateString()}</span>
                        {app.applied_at && (
                          <>
                            <span>•</span>
                            <span>Applied: {new Date(app.applied_at).toLocaleDateString()}</span>
                          </>
                        )}
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

                      {/* View Job Details Toggle */}
                      {app.job_description && (
                        <div className="mt-3">
                          <button
                            onClick={() =>
                              setExpandedJobDetails(
                                expandedJobDetails === app.application_id ? null : app.application_id
                              )
                            }
                            className="flex items-center gap-1 text-sm text-cyan-400 hover:text-cyan-300 transition-colors"
                          >
                            {expandedJobDetails === app.application_id ? (
                              <ChevronUp className="w-4 h-4" />
                            ) : (
                              <ChevronDown className="w-4 h-4" />
                            )}
                            <Info className="w-4 h-4" />
                            {expandedJobDetails === app.application_id ? "Hide" : "View"} job details
                          </button>

                          {expandedJobDetails === app.application_id && (
                            <div className="mt-4 p-4 rounded-lg bg-cyan-500/5 border border-cyan-500/20">
                              {/* Salary Section */}
                              <div className="mb-4 pb-3 border-b border-cyan-500/20">
                                <h5 className="text-sm font-medium text-cyan-400 flex items-center gap-2 mb-2">
                                  <DollarSign className="w-4 h-4" />
                                  Salary
                                </h5>
                                <p className={`text-base font-semibold ${app.salary_range && app.salary_range !== "Salary not listed" ? "text-emerald-400" : "text-muted-foreground"}`}>
                                  {app.salary_range || "Salary not listed"}
                                </p>
                              </div>
                              
                              {/* Job Description Section */}
                              <div>
                                <h5 className="text-sm font-medium text-cyan-400 flex items-center gap-2 mb-2">
                                  <FileText className="w-4 h-4" />
                                  Job Description
                                </h5>
                                <div className="max-h-80 overflow-y-auto pr-2 scrollbar-thin">
                                  <p className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">
                                    {app.job_description}
                                  </p>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {(app.optimized_resume || app.cover_letter) && (
                        <div className="mt-3">
                          <button
                            onClick={() =>
                              setExpandedApp(
                                expandedApp === app.application_id ? null : app.application_id
                              )
                            }
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
                                      onClick={() => setViewDocument({type: 'resume', content: app.optimized_resume, company: app.company || 'Company'})}
                                      className="h-7 text-xs border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20"
                                    >
                                      <FileText className="w-3 h-3 mr-1" />
                                      View & Copy
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
                                      onClick={() => setViewDocument({type: 'cover', content: app.cover_letter, company: app.company || 'Company'})}
                                      className="h-7 text-xs border-indigo-500/30 text-indigo-400 hover:bg-indigo-500/20"
                                    >
                                      <FileText className="w-3 h-3 mr-1" />
                                      View & Copy
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

                    <div className="flex flex-col gap-2">
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

                            {isAutoFillSupported(app.apply_link) && (
                              <Button
                                data-testid={`auto-fill-submit-btn-${i}`}
                                size="sm"
                                onClick={() =>
                                  handleAutoApplyClick(
                                    app.application_id,
                                    app.job_title,
                                    app.company,
                                    app.apply_link
                                  )
                                }
                                disabled={actionLoading === app.application_id || loadingPreview}
                                className="bg-purple-500 hover:bg-purple-600"
                                title="Auto-fill and submit the application form"
                              >
                                {actionLoading === app.application_id || loadingPreview ? (
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                  <>
                                    <Rocket className="w-4 h-4 mr-1" />
                                    Auto-Apply
                                  </>
                                )}
                              </Button>
                            )}

                            <Button
                              data-testid={`interview-prep-btn-${i}`}
                              size="sm"
                              onClick={() => handleInterviewPrep(app)}
                              className="bg-emerald-500 hover:bg-emerald-600"
                              title="Get interview preparation materials"
                            >
                              <GraduationCap className="w-4 h-4 mr-1" />
                              Interview Prep
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

                        {app.status === "ready_to_submit" && (
                          <>
                            <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/30 px-3 py-1">
                              ✓ Form Ready
                            </Badge>
                            <Button
                              data-testid={`open-to-submit-btn-${i}`}
                              size="sm"
                              onClick={() => window.open(app.apply_link, "_blank")}
                              className="bg-emerald-500 hover:bg-emerald-600"
                            >
                              <ExternalLink className="w-4 h-4 mr-1" />
                              Open & Submit
                            </Button>
                          </>
                        )}

                        {app.status === "approved" && (
                          <>
                            {isAutoFillSupported(app.apply_link) && (
                              <Button
                                data-testid={`auto-fill-approved-btn-${i}`}
                                size="sm"
                                onClick={() =>
                                  handleAutoApplyClick(
                                    app.application_id,
                                    app.job_title,
                                    app.company,
                                    app.apply_link
                                  )
                                }
                                disabled={actionLoading === app.application_id || loadingPreview}
                                className="bg-purple-500 hover:bg-purple-600"
                              >
                                {actionLoading === app.application_id || loadingPreview ? (
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                  <>
                                    <Rocket className="w-4 h-4 mr-1" />
                                    Auto-Apply
                                  </>
                                )}
                              </Button>
                            )}
                            <Button
                              data-testid={`submit-now-btn-${i}`}
                              size="sm"
                              onClick={() => handleSubmitNow(app)}
                              className="bg-indigo-500 hover:bg-indigo-600"
                            >
                              <Send className="w-4 h-4 mr-1" />
                              Submit Manually
                            </Button>
                            <Button
                              data-testid={`interview-prep-approved-btn-${i}`}
                              size="sm"
                              onClick={() => handleInterviewPrep(app)}
                              className="bg-emerald-500 hover:bg-emerald-600"
                              title="Get interview preparation materials"
                            >
                              <GraduationCap className="w-4 h-4 mr-1" />
                              Interview Prep
                            </Button>
                          </>
                        )}

                        {app.status === "applied" && (
                          <>
                            <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 px-3 py-1">
                              ✓ Applied
                            </Badge>
                            <Button
                              data-testid={`interview-prep-applied-btn-${i}`}
                              size="sm"
                              onClick={() => handleInterviewPrep(app)}
                              className="bg-emerald-500 hover:bg-emerald-600"
                              title="Prepare for your interview"
                            >
                              <GraduationCap className="w-4 h-4 mr-1" />
                              Interview Prep
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
                  </div>
                  
                  {/* What to Do Next - Only show for applied applications */}
                  {app.status === "applied" && (
                    <NextStepsCard 
                      application={app} 
                      onUpdate={fetchApplications}
                    />
                  )}
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
            <AlertDialogAction onClick={handleDelete} className="bg-red-500 hover:bg-red-600">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={showBulkConfirm} onOpenChange={setShowBulkConfirm}>
        <AlertDialogContent className="bg-background border-white/10">
          <AlertDialogHeader>
            <AlertDialogTitle>Approve All Pending Applications?</AlertDialogTitle>
            <AlertDialogDescription>
              This will approve and submit all {counts.pending} pending application
              {counts.pending !== 1 ? "s" : ""}. Each application will be marked as submitted with
              its optimized resume and cover letter (if generated).
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="border-white/10">Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleBulkApprove} className="bg-emerald-500 hover:bg-emerald-600">
              <Send className="w-4 h-4 mr-2" />
              Approve All ({counts.pending})
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Auto-Fill & Submit Confirmation Modal with Preview */}
      <Dialog open={!!confirmSubmit} onOpenChange={() => { setConfirmSubmit(null); setPreviewData(null); }}>
        <DialogContent className="bg-background border-white/10 max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-purple-400">
              <Rocket className="w-5 h-5" />
              Preview & Confirm Auto-Submit
            </DialogTitle>
            <DialogDescription>
              Review the data below before submitting your application
            </DialogDescription>
          </DialogHeader>
          
          {/* Job Info */}
          <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
            <div className="font-semibold text-foreground">{confirmSubmit?.jobTitle}</div>
            <div className="text-sm text-muted-foreground">{confirmSubmit?.company}</div>
          </div>
          
          {/* Preview Data Section */}
          <ScrollArea className="flex-1 max-h-[400px] pr-4">
            {loadingPreview ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-purple-400" />
                <span className="ml-2 text-muted-foreground">Loading your profile data...</span>
              </div>
            ) : previewData ? (
              <div className="space-y-3">
                <div className="text-sm font-semibold text-foreground mb-2">
                  📋 Data that will be filled:
                </div>
                
                {/* Personal Info */}
                {(previewData.personal_info?.full_name || previewData.personal_info?.email) && (
                  <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                    <div className="text-xs text-muted-foreground uppercase tracking-wide mb-2">Personal Info</div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      {previewData.personal_info?.full_name && (
                        <div><span className="text-muted-foreground">Name:</span> <span className="text-foreground">{previewData.personal_info.full_name}</span></div>
                      )}
                      {previewData.personal_info?.email && (
                        <div><span className="text-muted-foreground">Email:</span> <span className="text-foreground">{previewData.personal_info.email}</span></div>
                      )}
                      {previewData.personal_info?.phone && (
                        <div><span className="text-muted-foreground">Phone:</span> <span className="text-foreground">{previewData.personal_info.phone}</span></div>
                      )}
                    </div>
                  </div>
                )}
                
                {/* Location */}
                {previewData.personal_info?.location && (
                  <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                    <div className="text-xs text-muted-foreground uppercase tracking-wide mb-2">Location</div>
                    <div className="text-sm text-foreground">
                      {[previewData.personal_info.location.city, previewData.personal_info.location.state, previewData.personal_info.location.country].filter(Boolean).join(', ')}
                    </div>
                  </div>
                )}
                
                {/* Links */}
                {(previewData.personal_info?.linkedin || previewData.personal_info?.github || previewData.personal_info?.portfolio) && (
                  <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                    <div className="text-xs text-muted-foreground uppercase tracking-wide mb-2">Links</div>
                    <div className="space-y-1 text-sm">
                      {previewData.personal_info?.linkedin && (
                        <div><span className="text-muted-foreground">LinkedIn:</span> <span className="text-blue-400 truncate">{previewData.personal_info.linkedin}</span></div>
                      )}
                      {previewData.personal_info?.github && (
                        <div><span className="text-muted-foreground">GitHub:</span> <span className="text-blue-400 truncate">{previewData.personal_info.github}</span></div>
                      )}
                      {previewData.personal_info?.portfolio && (
                        <div><span className="text-muted-foreground">Portfolio:</span> <span className="text-blue-400 truncate">{previewData.personal_info.portfolio}</span></div>
                      )}
                    </div>
                  </div>
                )}
                
                {/* Work Authorization */}
                {previewData.questions && previewData.questions.some(q => q.field_type === 'work_authorization') && (
                  <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                    <div className="text-xs text-muted-foreground uppercase tracking-wide mb-2">Work Authorization</div>
                    {previewData.questions.filter(q => q.field_type === 'work_authorization').map((q, i) => (
                      <div key={i} className="text-sm text-foreground">{q.current_value || 'Not specified'}</div>
                    ))}
                  </div>
                )}
                
                {/* Resume */}
                {previewData.documents?.resume?.text && (
                  <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                    <div className="text-xs text-emerald-400 uppercase tracking-wide mb-2">Resume</div>
                    <div className="text-sm text-muted-foreground">
                      ✅ {previewData.documents.resume.original_filename || 'Resume'} will be uploaded
                    </div>
                  </div>
                )}
                
                {/* Cover Letter */}
                {previewData.documents?.cover_letter?.text && (
                  <div className="p-3 rounded-lg bg-indigo-500/10 border border-indigo-500/20">
                    <div className="text-xs text-indigo-400 uppercase tracking-wide mb-2">Cover Letter</div>
                    <div className="text-sm text-muted-foreground">
                      ✅ Custom cover letter will be included
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <AlertCircle className="w-8 h-8 mx-auto mb-2" />
                <p>Could not load preview data. You can still proceed.</p>
              </div>
            )}
          </ScrollArea>
          
          {/* Warning */}
          <div className="p-3 bg-amber-500/10 rounded-lg border border-amber-500/20 text-amber-400 text-sm">
            ⚠️ Clicking "Fill & Submit" will automatically submit your application. Make sure the data above is correct.
          </div>
          
          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-2 pt-2">
            <Button
              variant="outline"
              onClick={() => { setConfirmSubmit(null); setPreviewData(null); }}
              className="border-white/10"
            >
              Cancel
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                const { applicationId, jobTitle, company, applyLink } = confirmSubmit;
                setConfirmSubmit(null);
                setPreviewData(null);
                handleAutoFill(applicationId, jobTitle, company, applyLink);
              }}
              className="border-indigo-500/30 text-indigo-400 hover:bg-indigo-500/20"
            >
              <FileText className="w-4 h-4 mr-2" />
              Fill Only (No Submit)
            </Button>
            <Button
              onClick={() => {
                const { applicationId, jobTitle, company, applyLink } = confirmSubmit;
                setPreviewData(null);
                handleAutoFillAndSubmit(applicationId, jobTitle, company, applyLink);
              }}
              className="bg-purple-500 hover:bg-purple-600"
            >
              <Rocket className="w-4 h-4 mr-2" />
              Fill & Submit
            </Button>
          </div>
        </DialogContent>
      </Dialog>

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
                    <span className="ml-2 text-foreground">
                      {reviewApp?.location || "Not specified"}
                    </span>
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
                        onClick={() => copyToClipboard(reviewApp.optimized_resume, "resume")}
                        className="h-7 text-xs text-emerald-400 hover:bg-emerald-500/20"
                      >
                        {copiedField === "resume" ? (
                          <CheckCheck className="w-3 h-3 mr-1" />
                        ) : (
                          <Copy className="w-3 h-3 mr-1" />
                        )}
                        {copiedField === "resume" ? "Copied!" : "Copy"}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setViewDocument({type: 'resume', content: reviewApp.optimized_resume, company: reviewApp.company || 'Company'})}
                        className="h-7 text-xs border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20"
                      >
                        <FileText className="w-3 h-3 mr-1" />
                        View & Copy
                      </Button>
                    </div>
                  </div>
                  <pre className="text-xs text-muted-foreground whitespace-pre-wrap font-sans max-h-48 overflow-auto bg-black/20 p-3 rounded">
                    {reviewApp.optimized_resume}
                  </pre>
                </div>
              )}

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
                        onClick={() => copyToClipboard(reviewApp.cover_letter, "cover")}
                        className="h-7 text-xs text-indigo-400 hover:bg-indigo-500/20"
                      >
                        {copiedField === "cover" ? (
                          <CheckCheck className="w-3 h-3 mr-1" />
                        ) : (
                          <Copy className="w-3 h-3 mr-1" />
                        )}
                        {copiedField === "cover" ? "Copied!" : "Copy"}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setViewDocument({type: 'cover', content: reviewApp.cover_letter, company: reviewApp.company || 'Company'})}
                        className="h-7 text-xs border-indigo-500/30 text-indigo-400 hover:bg-indigo-500/20"
                      >
                        <FileText className="w-3 h-3 mr-1" />
                        View & Copy
                      </Button>
                    </div>
                  </div>
                  <pre className="text-xs text-muted-foreground whitespace-pre-wrap font-sans max-h-48 overflow-auto bg-black/20 p-3 rounded">
                    {reviewApp.cover_letter}
                  </pre>
                </div>
              )}

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
            <Button onClick={() => handleOpenApplication(reviewApp)} className="bg-cyan-500 hover:bg-cyan-600">
              <ExternalLink className="w-4 h-4 mr-2" />
              Open Application
            </Button>
          </div>
        </DialogContent>
      </Dialog>

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
                      onClick={() => copyToClipboard(autoFillScript, "autofill-script")}
                      className={`w-full ${
                        copiedField === "autofill-script"
                          ? "bg-emerald-500 hover:bg-emerald-600"
                          : "bg-indigo-500 hover:bg-indigo-600"
                      }`}
                    >
                      {copiedField === "autofill-script" ? (
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

              <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                <h4 className="text-sm font-medium text-foreground mb-3">Or Copy Manually:</h4>
                <div className="grid grid-cols-2 gap-3">
                  {submitApp?.optimized_resume && (
                    <Button
                      variant="outline"
                      onClick={() => copyToClipboard(submitApp.optimized_resume, "submit-resume")}
                      className="h-auto py-3 flex-col items-center gap-2 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20"
                    >
                      {copiedField === "submit-resume" ? (
                        <CheckCheck className="w-5 h-5" />
                      ) : (
                        <FileText className="w-5 h-5" />
                      )}
                      <span className="text-xs">
                        {copiedField === "submit-resume" ? "Resume Copied!" : "Copy Resume"}
                      </span>
                    </Button>
                  )}
                  {submitApp?.cover_letter && (
                    <Button
                      variant="outline"
                      onClick={() => copyToClipboard(submitApp.cover_letter, "submit-cover")}
                      className="h-auto py-3 flex-col items-center gap-2 border-indigo-500/30 text-indigo-400 hover:bg-indigo-500/20"
                    >
                      {copiedField === "submit-cover" ? (
                        <CheckCheck className="w-5 h-5" />
                      ) : (
                        <MessageSquare className="w-5 h-5" />
                      )}
                      <span className="text-xs">
                        {copiedField === "submit-cover" ? "Cover Letter Copied!" : "Copy Cover Letter"}
                      </span>
                    </Button>
                  )}
                </div>
              </div>

              <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                <h4 className="text-sm font-medium text-foreground mb-2">How to Use Auto-Fill:</h4>
                <ol className="text-sm text-muted-foreground space-y-1 list-decimal list-inside">
                  <li>Click &quot;Copy Auto-Fill Script&quot; above</li>
                  <li>Click &quot;Open Application Page&quot; below</li>
                  <li>
                    On the job site, press{" "}
                    <kbd className="px-1.5 py-0.5 bg-white/10 rounded text-xs">F12</kbd> to open Developer Tools
                  </li>
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

      {/* View Document Modal - Full page copy-paste view */}
      <Dialog open={!!viewDocument} onOpenChange={() => setViewDocument(null)}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className={viewDocument?.type === 'resume' ? 'text-emerald-400' : 'text-indigo-400'}>
              {viewDocument?.type === 'resume' ? 'Optimized Resume' : 'Cover Letter'} - {viewDocument?.company}
            </DialogTitle>
            <DialogDescription>
              Download as Word document or copy the text below
            </DialogDescription>
          </DialogHeader>
          
          <div className="flex gap-2 mb-4 flex-wrap">
            <Button
              onClick={() => downloadDocument(viewDocument?.content, viewDocument?.company, viewDocument?.type)}
              className={viewDocument?.type === 'resume' 
                ? 'bg-emerald-500 hover:bg-emerald-600' 
                : 'bg-indigo-500 hover:bg-indigo-600'}
            >
              <Download className="w-4 h-4 mr-2" />
              Download .docx
            </Button>
            <Button
              variant="outline"
              onClick={copyDocument}
              className="border-white/20"
            >
              <Copy className="w-4 h-4 mr-2" />
              Copy All Text
            </Button>
            <Button
              variant="ghost"
              onClick={() => {
                const textArea = document.getElementById('document-content');
                if (textArea) {
                  textArea.select();
                  toast.info("Text selected! Press Ctrl+C (or Cmd+C) to copy");
                }
              }}
            >
              Select All
            </Button>
          </div>

          <div className="flex-1 overflow-auto bg-white rounded-lg p-8 min-h-[400px] shadow-inner">
            <textarea
              id="document-content"
              readOnly
              value={viewDocument?.content || ''}
              className="w-full h-full min-h-[500px] text-black leading-relaxed font-sans resize-none border-none outline-none bg-transparent"
              style={{ 
                fontFamily: 'Calibri, "Segoe UI", Arial, sans-serif', 
                fontSize: '11pt', 
                lineHeight: '1.6',
                whiteSpace: 'pre-wrap'
              }}
            />
          </div>

          <div className="mt-4 text-center text-muted-foreground text-sm">
            Click &quot;Download .docx&quot; to save directly to your computer with formatting preserved
          </div>
        </DialogContent>
      </Dialog>

      {/* Auto-Fill Data Modal */}
      <Dialog open={!!autoFillData} onOpenChange={() => setAutoFillData(null)}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className={autoFillData?.submitted ? (autoFillData?.submissionConfirmed ? "text-emerald-400" : "text-amber-400") : "text-indigo-400"}>
              {autoFillData?.submitted 
                ? (autoFillData?.submissionConfirmed ? '🎉 Submission Likely Successful!' : '⚠️ Submit Clicked - Verify Email')
                : autoFillData?.playwrightSuccess 
                  ? '✅ Auto-Fill Complete' 
                  : '📋 Application Data'} - {autoFillData?.company}
            </DialogTitle>
            <DialogDescription>
              {autoFillData?.submitted
                ? (autoFillData?.submissionConfirmed 
                    ? `Confirmation page detected. Please check your email from ${autoFillData?.company} to confirm.`
                    : `Submit button clicked but confirmation not detected. Check your email to verify.`)
                : autoFillData?.playwrightSuccess 
                  ? `${autoFillData?.fieldsFilled?.length || 0} fields were automatically filled. Review and complete any remaining fields.`
                  : 'Copy each field to fill your application manually.'}
            </DialogDescription>
          </DialogHeader>
          
          {/* Success/Warning Banner */}
          {autoFillData?.submitted ? (
            <div className={`p-4 rounded-lg border mb-4 ${
              autoFillData?.submissionConfirmed 
                ? 'bg-gradient-to-r from-emerald-500/20 to-green-500/20 border-emerald-500/30'
                : 'bg-gradient-to-r from-amber-500/20 to-orange-500/20 border-amber-500/30'
            }`}>
              <div className={`flex items-center gap-2 ${autoFillData?.submissionConfirmed ? 'text-emerald-400' : 'text-amber-400'}`}>
                {autoFillData?.submissionConfirmed ? (
                  <CheckCircle className="w-6 h-6" />
                ) : (
                  <AlertCircle className="w-6 h-6" />
                )}
                <span className="font-bold text-lg">
                  {autoFillData?.submissionConfirmed ? 'Submission Likely Successful!' : 'Verify Submission via Email'}
                </span>
              </div>
              <div className={`text-sm mt-2 ${autoFillData?.submissionConfirmed ? 'text-emerald-300' : 'text-amber-300'}`}>
                {autoFillData?.fieldsFilled?.length || 0} fields were filled and submit was clicked.
              </div>
              
              {/* Final URL */}
              {autoFillData?.finalUrl && (
                <div className="text-xs text-muted-foreground mt-2">
                  <span className="font-medium">Final page URL:</span> {autoFillData.finalUrl}
                </div>
              )}
              
              <div className="text-xs text-foreground mt-3 p-2 bg-black/20 rounded">
                📧 <strong>Important:</strong> Check your email inbox (and spam folder) for confirmation from {autoFillData?.company}.
              </div>
            </div>
          ) : autoFillData?.playwrightSuccess ? (
            <div className="p-3 bg-emerald-500/20 rounded-lg border border-emerald-500/30 mb-4">
              <div className="flex items-center gap-2 text-emerald-400">
                <CheckCircle className="w-5 h-5" />
                <span className="font-semibold">{autoFillData?.message}</span>
              </div>
              {autoFillData?.fieldsFilled?.length > 0 && (
                <div className="text-sm text-emerald-300 mt-2">
                  Filled: {autoFillData.fieldsFilled.join(', ')}
                </div>
              )}
            </div>
          ) : (
            <div className="p-3 bg-amber-500/20 rounded-lg border border-amber-500/30 mb-4">
              <div className="flex items-center gap-2 text-amber-400">
                <AlertCircle className="w-5 h-5" />
                <span className="font-semibold">{autoFillData?.message || 'Manual entry required'}</span>
              </div>
              {autoFillData?.captchaDetected && (
                <div className="mt-2 text-sm text-amber-300">
                  🔒 The application page has a CAPTCHA. Click "Open Application" below to complete it in your browser - your data is ready to paste!
                </div>
              )}
              {autoFillData?.hint && !autoFillData?.captchaDetected && (
                <div className="mt-2 text-sm text-muted-foreground">
                  {autoFillData.hint}
                </div>
              )}
            </div>
          )}
          
          {/* Screenshot Evidence */}
          {autoFillData?.submitted && autoFillData?.screenshot && (
            <div className="mb-4">
              <div className="text-sm font-semibold text-foreground mb-2">📸 Screenshot of Final Page:</div>
              <div className="rounded-lg border border-white/10 overflow-hidden">
                <img 
                  src={`data:image/jpeg;base64,${autoFillData.screenshot}`} 
                  alt="Submission confirmation page"
                  className="w-full h-auto"
                />
              </div>
            </div>
          )}
          
          {!autoFillData?.submitted && (
            <div className="flex gap-2 mb-4">
              <Button
                onClick={() => {
                  if (autoFillData?.applyLink) {
                    window.open(autoFillData.applyLink, '_blank');
                  }
                }}
                className={autoFillData?.captchaDetected ? "bg-amber-500 hover:bg-amber-600" : "bg-indigo-500 hover:bg-indigo-600"}
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                {autoFillData?.captchaDetected ? "🔒 Open Application (Solve CAPTCHA)" : "Open Application"}
              </Button>
            </div>
          )}

          <ScrollArea className="flex-1 pr-4">
            <div className="space-y-3">
              {/* Section header for submitted applications */}
              {autoFillData?.submitted && (
                <div className="mb-4 text-sm font-semibold text-foreground">
                  📋 Data Submitted:
                </div>
              )}
              
              {/* Fields that need manual entry (failed or not filled) */}
              {autoFillData?.fieldsFailed?.length > 0 && !autoFillData?.submitted && (
                <div className="mb-4">
                  <div className="text-sm font-semibold text-amber-400 mb-2">⚠️ Fields needing manual entry:</div>
                  <div className="text-xs text-muted-foreground">
                    {autoFillData.fieldsFailed.join(', ')}
                  </div>
                </div>
              )}
              
              {autoFillData?.data && Object.entries(autoFillData.data)
                .filter(([key, value]) => key !== 'resume_text' && key !== 'cover_letter')
                .map(([key, value]) => {
                  const wasFilled = autoFillData?.fieldsFilled?.some(f => 
                    f.toLowerCase().replace(/\s+/g, '_') === key.toLowerCase() ||
                    f.toLowerCase().includes(key.replace(/_/g, ' ').toLowerCase())
                  );
                  
                  return (
                    <div 
                      key={key} 
                      className={`flex items-center justify-between p-3 rounded-lg border ${
                        wasFilled 
                          ? 'bg-emerald-500/10 border-emerald-500/20' 
                          : value 
                            ? 'bg-white/5 border-white/10' 
                            : 'bg-white/5 border-white/10 opacity-50'
                      }`}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-muted-foreground uppercase tracking-wide">
                            {key.replace(/_/g, ' ')}
                          </span>
                          {wasFilled && (
                            <span className="text-xs bg-emerald-500/30 text-emerald-300 px-1.5 py-0.5 rounded">
                              Auto-filled
                            </span>
                          )}
                        </div>
                        <div className={`text-sm truncate mt-1 ${value ? 'text-foreground' : 'text-muted-foreground italic'}`}>
                          {value || 'Not provided'}
                        </div>
                      </div>
                      {value && (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => copyToClipboard(value, key)}
                          className="ml-2 flex-shrink-0"
                        >
                          {copiedField === key ? (
                            <CheckCheck className="w-4 h-4 text-emerald-400" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </Button>
                      )}
                    </div>
                  );
                })}
              
              {/* Resume and Cover Letter sections */}
              {autoFillData?.data?.resume_text && (
                <div className="mt-4 p-3 rounded-lg border bg-emerald-500/10 border-emerald-500/20">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-muted-foreground uppercase tracking-wide">Resume</span>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => copyToClipboard(autoFillData.data.resume_text, 'resume')}
                    >
                      {copiedField === 'resume' ? (
                        <><CheckCheck className="w-4 h-4 text-emerald-400 mr-1" /> Copied</>
                      ) : (
                        <><Copy className="w-4 h-4 mr-1" /> Copy Resume</>
                      )}
                    </Button>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {autoFillData.data.resume_text.length} characters ready to paste
                  </div>
                </div>
              )}
              
              {autoFillData?.data?.cover_letter && (
                <div className="p-3 rounded-lg border bg-indigo-500/10 border-indigo-500/20">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-muted-foreground uppercase tracking-wide">Cover Letter</span>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => copyToClipboard(autoFillData.data.cover_letter, 'cover_letter')}
                    >
                      {copiedField === 'cover_letter' ? (
                        <><CheckCheck className="w-4 h-4 text-emerald-400 mr-1" /> Copied</>
                      ) : (
                        <><Copy className="w-4 h-4 mr-1" /> Copy Cover Letter</>
                      )}
                    </Button>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {autoFillData.data.cover_letter.length} characters ready to paste
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          <div className="mt-4 p-3 bg-blue-500/10 rounded-lg border border-blue-500/20">
            <div className="flex items-start gap-2">
              <Lightbulb className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-blue-200">
                <strong>Next steps:</strong> Click &quot;Open Application&quot; to go to the job page. 
                {autoFillData?.playwrightSuccess 
                  ? ' The form should already be filled - just review and submit!'
                  : ' Use the copy buttons above to fill each field, then review and submit.'}
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Interview Prep Dialog */}
      <Dialog open={showInterviewPrep} onOpenChange={setShowInterviewPrep}>
        <DialogContent className="max-w-4xl h-[85vh] overflow-hidden flex flex-col bg-gray-50 p-0">
          <DialogHeader className="bg-white px-6 py-4 border-b flex-shrink-0">
            <DialogTitle className="flex items-center gap-2 text-indigo-600">
              <GraduationCap className="w-5 h-5" />
              Interview Preparation
            </DialogTitle>
            <DialogDescription>
              {interviewPrepApp && (
                <span className="text-gray-600">
                  Tailored prep for <strong className="text-gray-900">{interviewPrepApp.job_title}</strong> at{" "}
                  <strong className="text-gray-900">{interviewPrepApp.company}</strong>
                </span>
              )}
            </DialogDescription>
          </DialogHeader>

          {interviewPrepLoading ? (
            <div className="flex flex-col items-center justify-center flex-1 bg-white">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mb-4" />
              <p className="text-gray-600">Generating your personalized interview prep...</p>
              <p className="text-sm text-gray-400 mt-2">This may take 15-30 seconds</p>
            </div>
          ) : interviewPrepMaterials ? (
            <div className="flex-1 overflow-y-auto bg-white">
              <div className="p-6 space-y-6">
                {(() => {
                  const cleanText = interviewPrepMaterials
                    .replace(/\*\*/g, '')
                    .replace(/\*/g, '')
                    .replace(/#{1,4}\s*/g, '')
                    .replace(/---/g, '')
                    .replace(/___/g, '');
                  
                  const lines = cleanText.split('\n').filter(line => line.trim());
                  const sections = [];
                  let currentSection = null;
                  let currentQA = null;
                  
                  for (const line of lines) {
                    const trimmed = line.trim();
                    
                    if (trimmed.match(/^\d+\.\s+[A-Z\s]+$/) || 
                        (trimmed === trimmed.toUpperCase() && trimmed.length > 10 && !trimmed.includes('?'))) {
                      if (currentSection) sections.push(currentSection);
                      currentSection = {
                        title: trimmed.replace(/^\d+\.\s*/, ''),
                        items: []
                      };
                      currentQA = null;
                    }
                    else if (trimmed.endsWith('?')) {
                      if (currentQA && currentSection) {
                        currentSection.items.push(currentQA);
                      }
                      currentQA = {
                        question: trimmed,
                        answer: []
                      };
                    }
                    else if (currentQA && trimmed) {
                      const cleanLine = trimmed
                        .replace(/^[-•*]\s*/, '')
                        .replace(/^>\s*/, '')
                        .replace(/^\d+\.\s*/, '');
                      if (cleanLine) {
                        currentQA.answer.push(cleanLine);
                      }
                    }
                    else if (!currentQA && currentSection && trimmed) {
                      const cleanLine = trimmed.replace(/^[-•*]\s*/, '').replace(/^>\s*/, '');
                      if (cleanLine && !cleanLine.match(/^\d+\.\s*$/)) {
                        currentSection.items.push({ tip: cleanLine });
                      }
                    }
                  }
                  
                  if (currentQA && currentSection) {
                    currentSection.items.push(currentQA);
                  }
                  if (currentSection) sections.push(currentSection);
                  
                  if (sections.length === 0) {
                    return (
                      <div className="bg-white rounded-xl p-6 border border-gray-200">
                        <p className="text-gray-900 leading-relaxed whitespace-pre-wrap">
                          {cleanText}
                        </p>
                      </div>
                    );
                  }
                  
                  return sections.map((section, sIdx) => (
                    <div key={sIdx} className="space-y-4">
                      <div className="flex items-center gap-3 mb-4">
                        <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center">
                          <span className="text-white font-bold text-sm">{sIdx + 1}</span>
                        </div>
                        <h2 className="text-xl font-bold text-indigo-600 uppercase tracking-wide">
                          {section.title}
                        </h2>
                      </div>
                      
                      <div className="space-y-4 ml-2">
                        {section.items.map((item, qIdx) => (
                          item.question ? (
                            <div 
                              key={qIdx} 
                              className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm"
                            >
                              <div className="bg-indigo-100 px-5 py-4 border-b border-indigo-200">
                                <div className="flex items-start gap-3">
                                  <span className="bg-indigo-600 text-white text-xs font-bold px-2.5 py-1.5 rounded mt-0.5 uppercase tracking-wide">
                                    Q
                                  </span>
                                  <p className="text-gray-900 font-bold text-base leading-relaxed">
                                    {item.question}
                                  </p>
                                </div>
                              </div>
                              
                              <div className="px-5 py-4 bg-emerald-50">
                                <div className="flex items-start gap-3">
                                  <span className="bg-emerald-600 text-white text-xs font-bold px-2.5 py-1.5 rounded mt-0.5 uppercase tracking-wide">
                                    A
                                  </span>
                                  <div className="space-y-2 flex-1">
                                    {item.answer.map((line, lIdx) => (
                                      <p key={lIdx} className="text-gray-700 leading-relaxed">
                                        {line}
                                      </p>
                                    ))}
                                    {item.answer.length === 0 && (
                                      <p className="text-gray-500 italic">
                                        Prepare your own answer based on your experience.
                                      </p>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </div>
                          ) : item.tip ? (
                            <div 
                              key={qIdx}
                              className="bg-amber-50 rounded-xl px-5 py-4 border border-amber-200"
                            >
                              <div className="flex items-start gap-3">
                                <Lightbulb className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
                                <p className="text-gray-800 leading-relaxed">{item.tip}</p>
                              </div>
                            </div>
                          ) : null
                        ))}
                      </div>
                    </div>
                  ));
                })()}
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center flex-1 text-gray-500 bg-white">
              <AlertCircle className="w-8 h-8 mb-4" />
              <p>No prep materials available. Try again.</p>
            </div>
          )}

          <div className="flex justify-end gap-2 p-4 bg-white border-t border-gray-200 flex-shrink-0">
            <Button
              variant="outline"
              onClick={() => {
                if (interviewPrepMaterials) {
                  navigator.clipboard.writeText(interviewPrepMaterials);
                  toast.success("Interview prep copied to clipboard!");
                }
              }}
              disabled={!interviewPrepMaterials}
              className="border-gray-300 text-gray-700 hover:bg-gray-100"
            >
              <Copy className="w-4 h-4 mr-2" />
              Copy All
            </Button>
            <Button
              onClick={() => handleInterviewPrep(interviewPrepApp)}
              disabled={interviewPrepLoading}
              className="bg-indigo-500 hover:bg-indigo-600 text-white"
            >
              {interviewPrepLoading ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Wand2 className="w-4 h-4 mr-2" />
              )}
              Regenerate
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
