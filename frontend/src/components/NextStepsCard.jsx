import { useState, useEffect } from "react";
import { API } from "@/App";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Building,
  Users,
  MessageSquare,
  HelpCircle,
  Target,
  Clock,
  Copy,
  ExternalLink,
  Loader2,
  Wand2,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Linkedin,
  CalendarClock,
} from "lucide-react";
import { toast } from "sonner";

const STEP_CONFIG = {
  follow_company: {
    icon: Building,
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/20",
  },
  find_recruiter: {
    icon: Users,
    color: "text-purple-400",
    bgColor: "bg-purple-500/10",
    borderColor: "border-purple-500/20",
  },
  send_message: {
    icon: MessageSquare,
    color: "text-cyan-400",
    bgColor: "bg-cyan-500/10",
    borderColor: "border-cyan-500/20",
  },
  prep_interview: {
    icon: HelpCircle,
    color: "text-amber-400",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/20",
  },
  track_outcome: {
    icon: Target,
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/20",
  },
  follow_up: {
    icon: Clock,
    color: "text-rose-400",
    bgColor: "bg-rose-500/10",
    borderColor: "border-rose-500/20",
  },
};

const OUTCOME_OPTIONS = [
  { value: "pending", label: "Pending Response" },
  { value: "interview_scheduled", label: "Interview Scheduled" },
  { value: "rejected", label: "Rejected" },
  { value: "offer", label: "Offer Received" },
];

export default function NextStepsCard({ application, onUpdate }) {
  const [nextSteps, setNextSteps] = useState(null);
  const [progress, setProgress] = useState({ completed: 0, total: 6, percentage: 0 });
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);
  const [generatingContent, setGeneratingContent] = useState(null);
  const [viewContent, setViewContent] = useState(null);
  const [updatingStep, setUpdatingStep] = useState(null);

  useEffect(() => {
    if (application?.application_id) {
      fetchNextSteps();
    }
  }, [application?.application_id]);

  const fetchNextSteps = async () => {
    try {
      const response = await fetch(
        `${API}/applications/${application.application_id}/next-steps`,
        { credentials: "include" }
      );
      if (response.ok) {
        const data = await response.json();
        setNextSteps(data.next_steps);
        setProgress(data.progress);
      }
    } catch (error) {
      console.error("Failed to fetch next steps:", error);
    } finally {
      setLoading(false);
    }
  };

  const updateStep = async (stepId, updates) => {
    setUpdatingStep(stepId);
    try {
      const response = await fetch(
        `${API}/applications/${application.application_id}/next-steps`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ step_id: stepId, ...updates }),
        }
      );

      if (response.ok) {
        const data = await response.json();
        setNextSteps(data.next_steps);
        setProgress(data.progress);
        if (onUpdate) onUpdate();
        toast.success("Progress updated!");
      }
    } catch (error) {
      toast.error("Failed to update step");
    } finally {
      setUpdatingStep(null);
    }
  };

  const generateContent = async (stepId, contentType = null) => {
    setGeneratingContent(stepId);
    try {
      const response = await fetch(
        `${API}/applications/${application.application_id}/next-steps/generate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ step_id: stepId, content_type: contentType }),
        }
      );

      if (response.ok) {
        const data = await response.json();
        
        // Update local state
        setNextSteps(prev => ({
          ...prev,
          [stepId]: {
            ...prev[stepId],
            ...(stepId === "send_message" 
              ? { generated_content: data.generated_content }
              : { generated_questions: data.generated_questions }
            ),
          },
        }));

        // Show the generated content
        setViewContent({
          stepId,
          contentType,
          content: stepId === "send_message" 
            ? data.generated_content 
            : data.generated_questions,
        });

        toast.success("Content generated!");
      } else {
        throw new Error("Failed to generate content");
      }
    } catch (error) {
      toast.error("Failed to generate content");
    } finally {
      setGeneratingContent(null);
    }
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success("Copied to clipboard!");
    } catch (error) {
      toast.error("Failed to copy");
    }
  };

  const openLinkedInSearch = (type) => {
    const company = encodeURIComponent(application.company || "");
    const jobTitle = encodeURIComponent(application.job_title || "");
    
    let url;
    if (type === "company") {
      url = `https://www.linkedin.com/search/results/companies/?keywords=${company}`;
    } else if (type === "recruiter") {
      url = `https://www.linkedin.com/search/results/people/?keywords=${company}%20recruiter%20OR%20hiring%20manager%20OR%20talent%20acquisition`;
    }
    
    window.open(url, "_blank");
  };

  const setFollowUpReminder = () => {
    const reminderDate = new Date();
    reminderDate.setDate(reminderDate.getDate() + 7);
    const dateString = reminderDate.toISOString().split("T")[0];
    
    updateStep("follow_up", { reminder_date: dateString, completed: true });
    toast.success(`Reminder set for ${reminderDate.toLocaleDateString()}`);
  };

  if (loading) {
    return (
      <Card className="glass-light mt-4 animate-pulse">
        <CardContent className="p-4">
          <div className="h-20 bg-white/5 rounded-lg" />
        </CardContent>
      </Card>
    );
  }

  if (!nextSteps) return null;

  const stepOrder = ["follow_company", "find_recruiter", "send_message", "prep_interview", "track_outcome", "follow_up"];

  return (
    <>
      <Card className="glass-light mt-4 border-emerald-500/20" data-testid="next-steps-card">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-semibold text-emerald-400 flex items-center gap-2">
              <CheckCircle className="w-5 h-5" />
              What to Do Next
            </CardTitle>
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground">
                {progress.completed}/{progress.total} completed
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setExpanded(!expanded)}
                className="h-8 w-8 p-0"
              >
                {expanded ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </Button>
            </div>
          </div>
          <Progress value={progress.percentage} className="h-2 mt-2" />
        </CardHeader>

        {expanded && (
          <CardContent className="pt-2">
            <div className="space-y-3">
              {stepOrder.map((stepId) => {
                const step = nextSteps[stepId];
                const config = STEP_CONFIG[stepId];
                const Icon = config.icon;
                const isUpdating = updatingStep === stepId;
                const isGenerating = generatingContent === stepId;

                return (
                  <div
                    key={stepId}
                    className={`p-3 rounded-lg ${config.bgColor} border ${config.borderColor} transition-all`}
                    data-testid={`next-step-${stepId}`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex items-center gap-2 pt-0.5">
                        <Checkbox
                          checked={step.completed}
                          disabled={isUpdating}
                          onCheckedChange={(checked) =>
                            updateStep(stepId, { completed: checked })
                          }
                          className="border-white/30"
                        />
                        <Icon className={`w-4 h-4 ${config.color}`} />
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className={`font-medium text-sm ${step.completed ? "line-through text-muted-foreground" : "text-foreground"}`}>
                          {step.title}
                        </div>
                        <div className="text-xs text-muted-foreground mt-0.5">
                          {step.description}
                        </div>

                        {/* Step-specific content */}
                        <div className="flex flex-wrap items-center gap-2 mt-2">
                          {stepId === "follow_company" && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => openLinkedInSearch("company")}
                              className="h-7 text-xs border-blue-500/30 text-blue-400 hover:bg-blue-500/20"
                            >
                              <Linkedin className="w-3 h-3 mr-1" />
                              Open LinkedIn
                            </Button>
                          )}

                          {stepId === "find_recruiter" && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => openLinkedInSearch("recruiter")}
                              className="h-7 text-xs border-purple-500/30 text-purple-400 hover:bg-purple-500/20"
                            >
                              <Users className="w-3 h-3 mr-1" />
                              Search LinkedIn
                            </Button>
                          )}

                          {stepId === "send_message" && (
                            <>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => generateContent("send_message", "linkedin_message")}
                                disabled={isGenerating}
                                className="h-7 text-xs border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/20"
                              >
                                {isGenerating ? (
                                  <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                                ) : (
                                  <Wand2 className="w-3 h-3 mr-1" />
                                )}
                                Generate Message
                              </Button>
                              {step.generated_content && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() =>
                                    setViewContent({
                                      stepId: "send_message",
                                      content: step.generated_content,
                                    })
                                  }
                                  className="h-7 text-xs border-white/20"
                                >
                                  <Copy className="w-3 h-3 mr-1" />
                                  View & Copy
                                </Button>
                              )}
                            </>
                          )}

                          {stepId === "prep_interview" && (
                            <>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => generateContent("prep_interview")}
                                disabled={isGenerating}
                                className="h-7 text-xs border-amber-500/30 text-amber-400 hover:bg-amber-500/20"
                              >
                                {isGenerating ? (
                                  <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                                ) : (
                                  <Wand2 className="w-3 h-3 mr-1" />
                                )}
                                Generate Questions
                              </Button>
                              {step.generated_questions && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() =>
                                    setViewContent({
                                      stepId: "prep_interview",
                                      content: step.generated_questions,
                                    })
                                  }
                                  className="h-7 text-xs border-white/20"
                                >
                                  <Copy className="w-3 h-3 mr-1" />
                                  View & Copy
                                </Button>
                              )}
                            </>
                          )}

                          {stepId === "track_outcome" && (
                            <Select
                              value={step.outcome || "pending"}
                              onValueChange={(value) =>
                                updateStep("track_outcome", { outcome: value, completed: value !== "pending" })
                              }
                            >
                              <SelectTrigger className="h-7 w-40 text-xs border-emerald-500/30">
                                <SelectValue placeholder="Select outcome" />
                              </SelectTrigger>
                              <SelectContent>
                                {OUTCOME_OPTIONS.map((option) => (
                                  <SelectItem key={option.value} value={option.value}>
                                    {option.label}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          )}

                          {stepId === "follow_up" && (
                            <>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={setFollowUpReminder}
                                disabled={step.completed}
                                className="h-7 text-xs border-rose-500/30 text-rose-400 hover:bg-rose-500/20"
                              >
                                <CalendarClock className="w-3 h-3 mr-1" />
                                Set 7-Day Reminder
                              </Button>
                              {step.reminder_date && (
                                <span className="text-xs text-muted-foreground">
                                  Reminder: {new Date(step.reminder_date).toLocaleDateString()}
                                </span>
                              )}
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        )}
      </Card>

      {/* View Content Dialog */}
      <Dialog open={!!viewContent} onOpenChange={() => setViewContent(null)}>
        <DialogContent className="bg-background border-white/10 max-w-2xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {viewContent?.stepId === "send_message" ? (
                <>
                  <MessageSquare className="w-5 h-5 text-cyan-400" />
                  Generated Message
                </>
              ) : (
                <>
                  <HelpCircle className="w-5 h-5 text-amber-400" />
                  Interview Prep Questions
                </>
              )}
            </DialogTitle>
            <DialogDescription>
              {viewContent?.stepId === "send_message"
                ? "Copy this message to send to the recruiter or hiring manager"
                : "Review these questions to prepare for your interview"}
            </DialogDescription>
          </DialogHeader>

          <ScrollArea className="max-h-[50vh] pr-4">
            <div className="p-4 rounded-lg bg-white/5 border border-white/10">
              <pre className="whitespace-pre-wrap text-sm text-foreground font-sans leading-relaxed">
                {viewContent?.content}
              </pre>
            </div>
          </ScrollArea>

          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="outline"
              onClick={() => setViewContent(null)}
              className="border-white/10"
            >
              Close
            </Button>
            <Button
              onClick={() => copyToClipboard(viewContent?.content)}
              className="bg-indigo-500 hover:bg-indigo-600"
            >
              <Copy className="w-4 h-4 mr-2" />
              Copy to Clipboard
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
