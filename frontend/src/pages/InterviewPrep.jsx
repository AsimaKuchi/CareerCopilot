import { useState } from "react";
import { API } from "@/App";
import { apiFetch } from "@/utils/apiFetch";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import Navbar from "@/components/Navbar";
import {
  Sparkles,
  Briefcase,
  Building,
  Loader2,
  MessageSquare,
  Target,
  Lightbulb,
  CheckCircle,
  ChevronRight,
  RefreshCw,
  ChevronDown,
} from "lucide-react";
import { toast } from "sonner";

export default function InterviewPrep({ user }) {
  const [jobTitle, setJobTitle] = useState("");
  const [company, setCompany] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [prepMaterials, setPrepMaterials] = useState("");
  const [loading, setLoading] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  // Accumulate all questions the user has already seen so the AI gives
  // fresh ones on every regenerate.
  const [seenQuestions, setSeenQuestions] = useState([]);

  const extractQuestions = (markdown) => {
    if (!markdown) return [];
    // Pull every #### header line (questions) + any line ending in ?
    const lines = markdown.split("\n");
    const questions = [];
    for (const raw of lines) {
      const line = raw.trim();
      if (line.startsWith("####")) {
        const q = line.replace(/^#+\s*/, "").trim();
        if (q) questions.push(q);
      } else if (line.endsWith("?") && line.length > 15 && line.length < 250) {
        questions.push(line);
      }
    }
    return questions;
  };

  const callPrepEndpoint = async ({ excluded = [], variation = null } = {}, onChunk) => {
    const response = await apiFetch(`${API}/ai/interview-prep`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        job_title: jobTitle.trim(),
        company: company.trim(),
        job_description: jobDescription.trim() || `${jobTitle} position at ${company}`,
        excluded_questions: excluded,
        variation: variation,
      }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      const detail = error.detail;
      throw new Error(typeof detail === "object" ? detail?.message : detail || "Failed to generate prep materials");
    }
    // The backend now streams text/plain. Read incrementally so the user
    // sees content within ~1s instead of waiting for the full 8000-char doc.
    const reader = response.body?.getReader();
    if (!reader) {
      // No streaming available (e.g. polyfill) - fall back to text()
      const text = await response.text();
      onChunk?.(text);
      return { prep_materials: text };
    }
    const decoder = new TextDecoder();
    let full = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      full += chunk;
      onChunk?.(full);
    }
    return { prep_materials: full };
  };

  const generatePrep = async () => {
    if (!jobTitle.trim() || !company.trim()) {
      toast.error("Please enter job title and company");
      return;
    }
    setLoading(true);
    setPrepMaterials(""); // clear previous so the streaming pane fills from scratch
    try {
      const data = await callPrepEndpoint({}, (partial) => setPrepMaterials(partial));
      setSeenQuestions(extractQuestions(data.prep_materials));
      toast.success("Interview prep materials generated!");
    } catch (error) {
      toast.error(error.message || "Failed to generate prep materials");
    } finally {
      setLoading(false);
    }
  };

  const regeneratePrep = async (variation = null) => {
    if (!jobTitle.trim() || !company.trim()) {
      toast.error("Please enter job title and company");
      return;
    }
    setRegenerating(true);
    setPrepMaterials(""); // clear previous so user sees the new batch stream in
    try {
      const data = await callPrepEndpoint(
        { excluded: seenQuestions, variation },
        (partial) => setPrepMaterials(partial)
      );
      const newQuestions = extractQuestions(data.prep_materials);
      setSeenQuestions((prev) => [...prev, ...newQuestions]);
      toast.success(
        variation
          ? `New ${variation.replace("_", " ")} questions generated!`
          : "Fresh batch of questions generated!"
      );
    } catch (error) {
      toast.error(error.message || "Failed to regenerate");
    } finally {
      setRegenerating(false);
    }
  };

  const tips = [
    {
      icon: Target,
      title: "Research the Company",
      description: "Know their mission, values, recent news, and products",
    },
    {
      icon: MessageSquare,
      title: "Practice STAR Method",
      description: "Structure answers: Situation, Task, Action, Result",
    },
    {
      icon: Lightbulb,
      title: "Prepare Questions",
      description: "Ask about team culture, growth opportunities, and challenges",
    },
    {
      icon: CheckCircle,
      title: "Review Your Resume",
      description: "Be ready to discuss every point on your resume",
    },
  ];

  return (
    <div className="min-h-screen bg-background" data-testid="interview-prep-page">
      <Navbar user={user} />
      
      <div className="hero-glow opacity-30" />

      <main className="relative z-10 max-w-6xl mx-auto px-6 py-8">
        <div className="mb-8 animate-fade-in">
          <h1 className="text-3xl font-bold text-foreground mb-2">Interview Preparation</h1>
          <p className="text-muted-foreground">
            Get AI-powered interview tips and practice questions tailored to your target role
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Input Form */}
          <div className="lg:col-span-1 space-y-6">
            <Card className="glass-light animate-fade-in" data-testid="prep-form">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-indigo-400" />
                  Generate Prep Materials
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label className="text-gray-900 mb-2 block">Job Title *</Label>
                  <div className="relative">
                    <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <Input
                      data-testid="job-title-input"
                      placeholder="e.g., Software Engineer"
                      value={jobTitle}
                      onChange={(e) => setJobTitle(e.target.value)}
                      className="pl-10 bg-white border-gray-200"
                    />
                  </div>
                </div>

                <div>
                  <Label className="text-gray-900 mb-2 block">Company *</Label>
                  <div className="relative">
                    <Building className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <Input
                      data-testid="company-input"
                      placeholder="e.g., Google"
                      value={company}
                      onChange={(e) => setCompany(e.target.value)}
                      className="pl-10 bg-white border-gray-200"
                    />
                  </div>
                </div>

                <div>
                  <Label className="text-gray-900 mb-2 block">Job Description (Optional)</Label>
                  <Textarea
                    data-testid="job-description-input"
                    placeholder="Paste the job description for more targeted prep..."
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    rows={5}
                    className="bg-white border-gray-200"
                  />
                </div>

                <Button
                  data-testid="generate-prep-btn"
                  onClick={generatePrep}
                  disabled={loading}
                  className="w-full bg-indigo-500 hover:bg-indigo-600"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      Generate Prep Materials
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Quick Tips */}
            <Card className="glass-light animate-fade-in-delay-1" data-testid="quick-tips">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lightbulb className="w-5 h-5 text-amber-400" />
                  Quick Tips
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {tips.map((tip, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gray-50 flex items-center justify-center flex-shrink-0">
                      <tip.icon className="w-4 h-4 text-indigo-500" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 text-sm">{tip.title}</p>
                      <p className="text-xs text-gray-500">{tip.description}</p>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Results */}
          <div className="lg:col-span-2">
            <Card className="glass-light h-full animate-fade-in-delay-2" data-testid="prep-results">
              <CardHeader>
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <CardTitle className="flex items-center gap-2">
                    <MessageSquare className="w-5 h-5 text-emerald-400" />
                    Interview Preparation Guide
                  </CardTitle>
                  {prepMaterials && (
                    <div className="flex items-center gap-2">
                      <Button
                        data-testid="regenerate-prep-btn"
                        size="sm"
                        variant="outline"
                        onClick={() => regeneratePrep(null)}
                        disabled={regenerating || loading}
                        className="border-indigo-200 text-indigo-600 hover:bg-indigo-50"
                        title="Get a fresh batch of different questions"
                      >
                        {regenerating ? (
                          <Loader2 className="w-4 h-4 animate-spin mr-1.5" />
                        ) : (
                          <RefreshCw className="w-4 h-4 mr-1.5" />
                        )}
                        New Questions
                      </Button>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            data-testid="variation-dropdown-btn"
                            size="sm"
                            variant="outline"
                            disabled={regenerating || loading}
                            className="border-indigo-200 text-indigo-600 hover:bg-indigo-50"
                          >
                            By Theme
                            <ChevronDown className="w-3.5 h-3.5 ml-1" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-56">
                          <DropdownMenuItem
                            data-testid="variation-behavioral"
                            onClick={() => regeneratePrep("behavioral")}
                          >
                            Behavioral & Situational
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            data-testid="variation-technical"
                            onClick={() => regeneratePrep("technical")}
                          >
                            Deep Technical
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            data-testid="variation-leadership"
                            onClick={() => regeneratePrep("leadership")}
                          >
                            Leadership & Strategy
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            data-testid="variation-edge-cases"
                            onClick={() => regeneratePrep("edge_cases")}
                          >
                            Tough / Curveball
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  )}
                </div>
                {seenQuestions.length > 0 && (
                  <p className="text-xs text-muted-foreground mt-2">
                    You've reviewed {seenQuestions.length} unique question
                    {seenQuestions.length === 1 ? "" : "s"} so far
                  </p>
                )}
              </CardHeader>
              <CardContent>
                {prepMaterials ? (
                  <ScrollArea className="h-[600px] pr-4">
                    <div className="space-y-6">
                      {(() => {
                        // Parse the prep materials into Q&A format
                        const cleanText = prepMaterials
                          .replace(/\*\*/g, '')  // Remove **bold**
                          .replace(/\*/g, '')    // Remove *italic*
                          .replace(/#{1,4}\s*/g, '')  // Remove # headers
                          .replace(/---/g, '')   // Remove horizontal rules
                          .replace(/___/g, '');
                        
                        const lines = cleanText.split('\n').filter(line => line.trim());
                        const qaItems = [];
                        let currentQA = null;
                        let currentSection = null;
                        
                        for (let i = 0; i < lines.length; i++) {
                          const trimmed = lines[i].trim();
                          
                          // Section headers (numbered or all caps)
                          if (trimmed.match(/^\d+\.\s+[A-Z\s]+$/) || 
                              (trimmed === trimmed.toUpperCase() && trimmed.length > 10 && trimmed.length < 60 && !trimmed.includes('?'))) {
                            currentSection = trimmed.replace(/^\d+\.\s*/, '');
                            continue;
                          }
                          
                          // Questions end with ?
                          if (trimmed.endsWith('?')) {
                            // Save previous Q&A
                            if (currentQA) {
                              qaItems.push(currentQA);
                            }
                            currentQA = {
                              section: currentSection,
                              question: trimmed,
                              approach: null,
                              answer: []
                            };
                          }
                          // Suggested approach line
                          else if (trimmed.toLowerCase().startsWith('suggested approach:') || 
                                   trimmed.toLowerCase().startsWith('approach:') ||
                                   trimmed.toLowerCase().includes('star framework') ||
                                   trimmed.toLowerCase().includes('framework guidance')) {
                            if (currentQA) {
                              currentQA.approach = trimmed;
                            }
                          }
                          // Answer content
                          else if (currentQA && trimmed && !trimmed.match(/^\d+\.\s*$/)) {
                            const cleanLine = trimmed
                              .replace(/^[-•*]\s*/, '')
                              .replace(/^>\s*/, '')
                              .replace(/^\d+\.\s*/, '');
                            if (cleanLine) {
                              currentQA.answer.push(cleanLine);
                            }
                          }
                        }
                        
                        // Push last Q&A
                        if (currentQA) {
                          qaItems.push(currentQA);
                        }
                        
                        // If no Q&As parsed, show as simple text
                        if (qaItems.length === 0) {
                          return (
                            <div className="bg-slate-50 rounded-xl p-6 border border-slate-200">
                              <p className="text-slate-800 leading-relaxed whitespace-pre-wrap">
                                {cleanText}
                              </p>
                            </div>
                          );
                        }
                        
                        // Group by section
                        let lastSection = null;
                        
                        return qaItems.map((item, idx) => (
                          <div key={idx} className="space-y-3">
                            {/* Section header if changed */}
                            {item.section && item.section !== lastSection && (() => {
                              lastSection = item.section;
                              return (
                                <div className="flex items-center gap-3 mt-6 mb-4 first:mt-0">
                                  <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center shadow-sm">
                                    <span className="text-white font-bold text-sm">
                                      {qaItems.filter((q, i) => i <= idx && q.section).map(q => q.section).filter((v, i, a) => a.indexOf(v) === i).length}
                                    </span>
                                  </div>
                                  <h2 className="text-lg font-bold text-indigo-600 uppercase tracking-wide">
                                    {item.section}
                                  </h2>
                                </div>
                              );
                            })()}
                            
                            {/* Question Box */}
                            <div className="rounded-xl overflow-hidden border border-slate-200 shadow-sm">
                              {/* Question with Q badge */}
                              <div className="bg-slate-50 px-5 py-4">
                                <div className="flex items-start gap-3">
                                  <span className="bg-indigo-500 text-white text-xs font-bold px-2.5 py-1 rounded flex-shrink-0">
                                    Q
                                  </span>
                                  <p className="text-slate-900 font-semibold leading-relaxed">
                                    {item.question}
                                  </p>
                                </div>
                              </div>
                              
                              {/* Answer with A badge */}
                              <div className="bg-white px-5 py-4 border-t border-slate-100">
                                <div className="flex items-start gap-3">
                                  <span className="bg-emerald-500 text-white text-xs font-bold px-2.5 py-1 rounded flex-shrink-0">
                                    A
                                  </span>
                                  <div className="space-y-3 flex-1">
                                    {/* Suggested approach */}
                                    {item.approach && (
                                      <p className="text-slate-700 font-medium">
                                        {item.approach}
                                      </p>
                                    )}
                                    
                                    {/* Answer paragraphs */}
                                    {item.answer.map((line, lIdx) => (
                                      <p key={lIdx} className="text-slate-700 leading-relaxed">
                                        {line}
                                      </p>
                                    ))}
                                    
                                    {/* Empty answer placeholder */}
                                    {item.answer.length === 0 && !item.approach && (
                                      <p className="text-slate-500 italic">
                                        Prepare your own answer based on your experience.
                                      </p>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        ));
                      })()}
                    </div>
                  </ScrollArea>
                ) : (
                  <div className="flex flex-col items-center justify-center h-[500px] text-center">
                    <div className="w-20 h-20 rounded-2xl bg-gray-50 flex items-center justify-center mb-6">
                      <MessageSquare className="w-10 h-10 text-gray-400" />
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">
                      Ready to Prepare?
                    </h3>
                    <p className="text-gray-500 max-w-md mb-6">
                      Enter the job details on the left and our AI will generate 
                      comprehensive interview preparation materials including common 
                      questions, tips, and strategies.
                    </p>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <span>Enter job details</span>
                      <ChevronRight className="w-4 h-4" />
                      <span>Generate prep</span>
                      <ChevronRight className="w-4 h-4" />
                      <span>Ace your interview!</span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
