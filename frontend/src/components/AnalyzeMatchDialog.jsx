import { useState, useEffect } from "react";
import { API } from "@/App";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  CheckCircle,
  AlertTriangle,
  Tag,
  FileEdit,
  Loader2,
  Copy,
  ChevronDown,
  ChevronUp,
  Save,
  TrendingUp,
  Target,
  Lightbulb,
} from "lucide-react";
import { toast } from "sonner";

export default function AnalyzeMatchDialog({ job, open, onOpenChange }) {
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [personalNotes, setPersonalNotes] = useState("");
  const [savingNotes, setSavingNotes] = useState(false);
  const [expandedStrengths, setExpandedStrengths] = useState({});
  const [expandedOpportunities, setExpandedOpportunities] = useState({});
  const [expandedEdit, setExpandedEdit] = useState(null);

  useEffect(() => {
    if (open && job) {
      loadAnalysis();
    }
  }, [open, job]);

  const loadAnalysis = async () => {
    setLoading(true);
    try {
      // Try to get cached analysis first
      const response = await fetch(`${API}/jobs/${job.job_id}/compare`, {
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        setAnalysis(data.comparison_json);
        setPersonalNotes(data.personal_notes || "");
      } else if (response.status === 404) {
        // No cached analysis, generate new one
        await generateAnalysis();
      } else {
        throw new Error("Failed to load analysis");
      }
    } catch (error) {
      console.error("Error loading analysis:", error);
      toast.error("Failed to load analysis");
    } finally {
      setLoading(false);
    }
  };

  const generateAnalysis = async () => {
    try {
      const response = await fetch(`${API}/jobs/${job.job_id}/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          job_id: job.job_id,
          job_title: job.title,
          company: job.company,
          job_description: job.description || job.full_description || `${job.title} at ${job.company}`,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to generate analysis");
      }

      const data = await response.json();
      setAnalysis(data.comparison_json);
      setPersonalNotes(data.personal_notes || "");
      toast.success("Analysis generated successfully!");
    } catch (error) {
      console.error("Error generating analysis:", error);
      toast.error(error.message || "Failed to generate analysis");
      throw error;
    }
  };

  const saveNotes = async () => {
    setSavingNotes(true);
    try {
      const response = await fetch(`${API}/jobs/${job.job_id}/compare/notes`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ notes: personalNotes }),
      });

      if (!response.ok) {
        throw new Error("Failed to save notes");
      }

      toast.success("Notes saved!");
    } catch (error) {
      toast.error("Failed to save notes");
    } finally {
      setSavingNotes(false);
    }
  };

  const copyKeywords = () => {
    if (analysis?.keywords_to_include) {
      navigator.clipboard.writeText(analysis.keywords_to_include.join(", "));
      toast.success("Keywords copied to clipboard!");
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case "high":
        return "bg-red-500/10 text-red-400 border-red-500/20";
      case "medium":
        return "bg-yellow-500/10 text-yellow-400 border-yellow-500/20";
      case "low":
        return "bg-blue-500/10 text-blue-400 border-blue-500/20";
      default:
        return "bg-gray-500/10 text-gray-400 border-gray-500/20";
    }
  };

  const getReadinessColor = (level) => {
    if (level?.toLowerCase().includes("ready")) return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
    if (level?.toLowerCase().includes("light")) return "bg-blue-500/10 text-blue-400 border-blue-500/30";
    if (level?.toLowerCase().includes("moderate")) return "bg-yellow-500/10 text-yellow-400 border-yellow-500/30";
    return "bg-orange-500/10 text-orange-400 border-orange-500/30";
  };

  const toggleStrength = (idx) => {
    setExpandedStrengths(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  const toggleOpportunity = (idx) => {
    setExpandedOpportunities(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  if (!job) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl h-[90vh] flex flex-col p-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b border-white/10">
          <DialogTitle className="text-2xl">
            Analyze Match: {job.title} at {job.company}
          </DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="flex flex-col items-center justify-center flex-1">
            <Loader2 className="w-12 h-12 animate-spin text-indigo-500 mb-4" />
            <p className="text-muted-foreground">Analyzing your fit for this role...</p>
            <p className="text-sm text-muted-foreground mt-2">
              This may take 10-15 seconds
            </p>
          </div>
        ) : analysis ? (
          <div className="flex-1 overflow-y-auto px-6 py-4">
            <div className="space-y-6 pb-6">
              {/* Decision Summary */}
              {analysis.decision_summary && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                      <Target className="w-5 h-5 text-indigo-400" />
                      Decision Summary
                    </h3>
                    <Badge className={getReadinessColor(analysis.decision_summary.readiness_level)}>
                      {analysis.decision_summary.readiness_level}
                    </Badge>
                  </div>
                  
                  <div className="p-4 rounded-lg bg-indigo-500/5 border border-indigo-500/20 space-y-2">
                    <p className="text-sm text-foreground">
                      {analysis.decision_summary.overall_fit}
                    </p>
                    {analysis.decision_summary.primary_risk && (
                      <p className="text-sm text-muted-foreground">
                        <span className="font-medium text-orange-400">Primary consideration:</span> {analysis.decision_summary.primary_risk}
                      </p>
                    )}
                    <p className="text-sm font-medium text-indigo-400">
                      → {analysis.decision_summary.recommendation}
                    </p>
                  </div>
                </div>
              )}

              {/* Personal Notes */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Personal Notes</label>
                <Textarea
                  value={personalNotes}
                  onChange={(e) => setPersonalNotes(e.target.value)}
                  placeholder="Add your thoughts, questions, or follow-up items for this role..."
                  rows={3}
                  className="bg-white/5 border-white/10"
                />
                <Button
                  size="sm"
                  onClick={saveNotes}
                  disabled={savingNotes}
                  className="bg-indigo-500 hover:bg-indigo-600"
                >
                  {savingNotes ? (
                    <>
                      <Loader2 className="w-3 h-3 animate-spin mr-2" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="w-3 h-3 mr-2" />
                      Save Notes
                    </>
                  )}
                </Button>
              </div>

              {/* Two-column layout: Strengths & Improvement Opportunities */}
              <div className="grid md:grid-cols-2 gap-6">
                {/* Strengths */}
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-emerald-400" />
                    Your Strengths ({analysis.strengths?.length || 0})
                  </h3>
                  <div className="space-y-2">
                    {analysis.strengths?.map((strength, idx) => (
                      <div
                        key={idx}
                        className="rounded-lg bg-emerald-500/5 border border-emerald-500/20 overflow-hidden"
                      >
                        <div
                          className="p-3 cursor-pointer hover:bg-emerald-500/10 transition-colors"
                          onClick={() => toggleStrength(idx)}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1">
                              <h4 className="font-medium text-emerald-400 text-sm">
                                {strength.title}
                              </h4>
                              <p className="text-xs text-muted-foreground mt-1">
                                {strength.summary}
                              </p>
                            </div>
                            {expandedStrengths[idx] ? (
                              <ChevronUp className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                            ) : (
                              <ChevronDown className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                            )}
                          </div>
                        </div>
                        
                        {expandedStrengths[idx] && (
                          <div className="px-3 pb-3 space-y-2 border-t border-emerald-500/20">
                            <p className="text-sm text-muted-foreground pt-2">
                              {strength.why_it_matches}
                            </p>
                            {strength.evidence && strength.evidence.length > 0 && (
                              <div className="space-y-1">
                                <p className="text-xs font-medium text-emerald-400">Evidence:</p>
                                <ul className="space-y-1">
                                  {strength.evidence.map((ev, evIdx) => (
                                    <li key={evIdx} className="text-xs text-foreground/80 pl-4">
                                      • {ev}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Improvement Opportunities */}
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold flex items-center gap-2">
                    <Lightbulb className="w-5 h-5 text-amber-400" />
                    Improvement Opportunities ({analysis.improvement_opportunities?.length || 0})
                  </h3>
                  <div className="space-y-2">
                    {analysis.improvement_opportunities?.map((opp, idx) => (
                      <div
                        key={idx}
                        className="rounded-lg bg-amber-500/5 border border-amber-500/20 overflow-hidden"
                      >
                        <div
                          className="p-3 cursor-pointer hover:bg-amber-500/10 transition-colors"
                          onClick={() => toggleOpportunity(idx)}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <h4 className="font-medium text-amber-400 text-sm">
                                  {opp.title}
                                </h4>
                                <Badge className={getPriorityColor(opp.priority) + " text-xs px-1.5 py-0"}>
                                  {opp.priority}
                                </Badge>
                              </div>
                              <p className="text-xs text-muted-foreground">
                                {opp.summary}
                              </p>
                            </div>
                            {expandedOpportunities[idx] ? (
                              <ChevronUp className="w-4 h-4 text-amber-400 flex-shrink-0" />
                            ) : (
                              <ChevronDown className="w-4 h-4 text-amber-400 flex-shrink-0" />
                            )}
                          </div>
                        </div>
                        
                        {expandedOpportunities[idx] && (
                          <div className="px-3 pb-3 space-y-2 border-t border-amber-500/20">
                            <p className="text-sm text-muted-foreground pt-2">
                              <span className="font-medium">Why it matters:</span> {opp.why_it_matters}
                            </p>
                            <p className="text-sm text-foreground/80">
                              <span className="font-medium text-amber-400">How to improve:</span> {opp.fix}
                            </p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Keywords to Include */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold flex items-center gap-2">
                    <Tag className="w-5 h-5 text-blue-400" />
                    Keywords to Include
                  </h3>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={copyKeywords}
                    className="border-white/10"
                  >
                    <Copy className="w-3 h-3 mr-2" />
                    Copy Keywords
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {analysis.keywords_to_include?.map((keyword, idx) => (
                    <Badge
                      key={idx}
                      variant="outline"
                      className="bg-blue-500/10 text-blue-400 border-blue-500/20 px-3 py-1"
                    >
                      {keyword}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Suggested Resume Edits */}
              <div className="space-y-3">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <FileEdit className="w-5 h-5 text-purple-400" />
                  Suggested Resume Edits
                </h3>
                <div className="space-y-3">
                  {analysis.suggested_resume_edits?.map((edit, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-lg bg-purple-500/5 border border-purple-500/20"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-purple-400">
                          {edit.target_section}
                        </span>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() =>
                            setExpandedEdit(expandedEdit === idx ? null : idx)
                          }
                        >
                          {expandedEdit === idx ? (
                            <ChevronUp className="w-4 h-4" />
                          ) : (
                            <ChevronDown className="w-4 h-4" />
                          )}
                        </Button>
                      </div>

                      {expandedEdit === idx && (
                        <div className="space-y-3">
                          <div className="p-3 rounded bg-red-500/10 border border-red-500/20">
                            <p className="text-xs font-medium text-red-400 mb-1">
                              BEFORE:
                            </p>
                            <p className="text-sm text-foreground/80">{edit.before}</p>
                          </div>
                          <div className="p-3 rounded bg-green-500/10 border border-green-500/20">
                            <p className="text-xs font-medium text-green-400 mb-1">
                              AFTER:
                            </p>
                            <p className="text-sm text-foreground/80">{edit.after}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Disclaimer */}
              <p className="text-xs text-muted-foreground text-center pt-4 border-t border-white/10">
                Suggestions are based on your resume text and the job description.
                Always review and customize recommendations before applying.
              </p>
            </div>
          </ScrollArea>
        ) : (
          <div className="py-20 text-center">
            <p className="text-muted-foreground">No analysis available</p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
