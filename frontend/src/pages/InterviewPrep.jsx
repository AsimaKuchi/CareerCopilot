import { useState } from "react";
import { API } from "@/App";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
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
} from "lucide-react";
import { toast } from "sonner";

export default function InterviewPrep({ user }) {
  const [jobTitle, setJobTitle] = useState("");
  const [company, setCompany] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [prepMaterials, setPrepMaterials] = useState("");
  const [loading, setLoading] = useState(false);

  const generatePrep = async () => {
    if (!jobTitle.trim() || !company.trim()) {
      toast.error("Please enter job title and company");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API}/ai/interview-prep`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          job_title: jobTitle.trim(),
          company: company.trim(),
          job_description: jobDescription.trim() || `${jobTitle} position at ${company}`,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to generate prep materials");
      }

      const data = await response.json();
      setPrepMaterials(data.prep_materials);
      toast.success("Interview prep materials generated!");
    } catch (error) {
      toast.error(error.message || "Failed to generate prep materials");
    } finally {
      setLoading(false);
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
                  <Label className="text-foreground mb-2 block">Job Title *</Label>
                  <div className="relative">
                    <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      data-testid="job-title-input"
                      placeholder="e.g., Software Engineer"
                      value={jobTitle}
                      onChange={(e) => setJobTitle(e.target.value)}
                      className="pl-10 bg-white/5 border-white/10"
                    />
                  </div>
                </div>

                <div>
                  <Label className="text-foreground mb-2 block">Company *</Label>
                  <div className="relative">
                    <Building className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      data-testid="company-input"
                      placeholder="e.g., Google"
                      value={company}
                      onChange={(e) => setCompany(e.target.value)}
                      className="pl-10 bg-white/5 border-white/10"
                    />
                  </div>
                </div>

                <div>
                  <Label className="text-foreground mb-2 block">Job Description (Optional)</Label>
                  <Textarea
                    data-testid="job-description-input"
                    placeholder="Paste the job description for more targeted prep..."
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    rows={5}
                    className="bg-white/5 border-white/10"
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
                    <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center flex-shrink-0">
                      <tip.icon className="w-4 h-4 text-indigo-400" />
                    </div>
                    <div>
                      <p className="font-medium text-foreground text-sm">{tip.title}</p>
                      <p className="text-xs text-muted-foreground">{tip.description}</p>
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
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-emerald-400" />
                  Interview Preparation Guide
                </CardTitle>
              </CardHeader>
              <CardContent>
                {prepMaterials ? (
                  <ScrollArea className="h-[600px] pr-4">
                    <div className="space-y-6">
                      {(() => {
                        // Parse the prep materials into sections
                        const cleanText = prepMaterials
                          .replace(/\*\*/g, '')  // Remove **bold**
                          .replace(/\*/g, '')    // Remove *italic*
                          .replace(/#{1,4}\s*/g, '')  // Remove # headers
                          .replace(/---/g, '')   // Remove horizontal rules
                          .replace(/___/g, '');
                        
                        // Split into Q&A pairs
                        const lines = cleanText.split('\n').filter(line => line.trim());
                        const sections = [];
                        let currentSection = null;
                        let currentQA = null;
                        
                        for (const line of lines) {
                          const trimmed = line.trim();
                          
                          // Section headers (numbered like "1. COMMON QUESTIONS" or all caps)
                          if (trimmed.match(/^\d+\.\s+[A-Z\s]+$/) || 
                              (trimmed === trimmed.toUpperCase() && trimmed.length > 10 && !trimmed.includes('?'))) {
                            if (currentSection) sections.push(currentSection);
                            currentSection = {
                              title: trimmed.replace(/^\d+\.\s*/, ''),
                              items: []
                            };
                            currentQA = null;
                          }
                          // Questions (end with ?)
                          else if (trimmed.endsWith('?')) {
                            if (currentQA && currentSection) {
                              currentSection.items.push(currentQA);
                            }
                            currentQA = {
                              question: trimmed,
                              answer: []
                            };
                          }
                          // Answer content
                          else if (currentQA && trimmed) {
                            // Clean up bullet points
                            const cleanLine = trimmed
                              .replace(/^[-•*]\s*/, '')
                              .replace(/^>\s*/, '')
                              .replace(/^\d+\.\s*/, '');
                            if (cleanLine) {
                              currentQA.answer.push(cleanLine);
                            }
                          }
                          // If no current Q&A but has content, might be intro or tips
                          else if (!currentQA && currentSection && trimmed) {
                            const cleanLine = trimmed.replace(/^[-•*]\s*/, '').replace(/^>\s*/, '');
                            if (cleanLine && !cleanLine.match(/^\d+\.\s*$/)) {
                              currentSection.items.push({ tip: cleanLine });
                            }
                          }
                        }
                        
                        // Push last items
                        if (currentQA && currentSection) {
                          currentSection.items.push(currentQA);
                        }
                        if (currentSection) sections.push(currentSection);
                        
                        // If no sections parsed, show as simple text
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
                            {/* Section Title */}
                            <div className="flex items-center gap-3 mb-4">
                              <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center">
                                <span className="text-white font-bold text-sm">{sIdx + 1}</span>
                              </div>
                              <h2 className="text-xl font-bold text-indigo-600 uppercase tracking-wide">
                                {section.title}
                              </h2>
                            </div>
                            
                            {/* Q&A Items */}
                            <div className="space-y-4 ml-2">
                              {section.items.map((item, qIdx) => (
                                item.question ? (
                                  // Q&A Box
                                  <div 
                                    key={qIdx} 
                                    className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm"
                                  >
                                    {/* Question */}
                                    <div className="bg-indigo-50 px-5 py-4 border-b border-gray-200">
                                      <div className="flex items-start gap-3">
                                        <span className="bg-indigo-500 text-white text-xs font-bold px-2 py-1 rounded mt-0.5">
                                          Q
                                        </span>
                                        <p className="text-gray-900 font-semibold text-base leading-relaxed">
                                          {item.question}
                                        </p>
                                      </div>
                                    </div>
                                    
                                    {/* Answer */}
                                    <div className="px-5 py-4 bg-white">
                                      <div className="flex items-start gap-3">
                                        <span className="bg-emerald-500 text-white text-xs font-bold px-2 py-1 rounded mt-0.5">
                                          A
                                        </span>
                                        <div className="space-y-2 flex-1">
                                          {item.answer.map((line, lIdx) => (
                                            <p key={lIdx} className="text-gray-800 leading-relaxed">
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
                                  // Tip Box
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
                  </ScrollArea>
                ) : (
                  <div className="flex flex-col items-center justify-center h-[500px] text-center">
                    <div className="w-20 h-20 rounded-2xl bg-white/5 flex items-center justify-center mb-6">
                      <MessageSquare className="w-10 h-10 text-muted-foreground" />
                    </div>
                    <h3 className="text-xl font-semibold text-foreground mb-2">
                      Ready to Prepare?
                    </h3>
                    <p className="text-muted-foreground max-w-md mb-6">
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
