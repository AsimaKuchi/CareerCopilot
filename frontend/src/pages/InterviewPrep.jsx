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
                    <div className="prose prose-invert prose-sm max-w-none">
                      <div 
                        className="interview-prep-content space-y-4"
                        dangerouslySetInnerHTML={{ 
                          __html: prepMaterials
                            .split('\n')
                            .map(line => {
                              // Horizontal rule
                              if (line.trim() === '---' || line.trim() === '___') {
                                return `<hr class="my-10 border-white/20" />`;
                              }
                              // ALL-CAPS numbered headers (1. COMMON INTERVIEW QUESTIONS)
                              else if (line.trim().match(/^\d+\.\s+[A-Z\s]+$/)) {
                                return `<h2 class="font-extrabold text-2xl text-indigo-400 mt-12 mb-6 uppercase tracking-wide">${line}</h2>`;
                              }
                              // Level-4 headers (#### Question)
                              else if (line.trim().startsWith('####')) {
                                const text = line.replace(/^####\s*/, '');
                                return `<h4 class="font-bold text-xl text-foreground mt-8 mb-3 leading-tight">${text}</h4>`;
                              }
                              // Level-3 headers
                              else if (line.trim().startsWith('###')) {
                                return `<h3 class="font-bold text-xl text-emerald-400 mt-8 mb-4">${line.replace(/^###\s*/, '')}</h3>`;
                              }
                              // Level-2 headers
                              else if (line.trim().startsWith('##')) {
                                return `<h2 class="font-bold text-2xl text-indigo-400 mt-10 mb-5">${line.replace(/^##\s*/, '')}</h2>`;
                              }
                              // Blockquotes (> Sample answer) - make text bolder
                              else if (line.trim().startsWith('>')) {
                                const content = line.trim().substring(1).trim();
                                return `<blockquote class="border-l-4 border-indigo-500 pl-5 py-3 my-4 text-gray-300 font-medium bg-white/5 rounded-r leading-relaxed">${content}</blockquote>`;
                              }
                              // Remove italics - just make it bold regular text
                              else if (line.trim().match(/^\*[^*]+\*$/) || line.trim().startsWith('Suggested') || line.trim().startsWith('STAR') || line.trim().startsWith('Approach')) {
                                const content = line.trim().replace(/^\*/, '').replace(/\*$/, '');
                                return `<p class="font-semibold text-base text-gray-300 mb-3 mt-2">${content}</p>`;
                              }
                              // Bold questions (lines ending with ?)
                              else if (line.trim().endsWith('?')) {
                                return `<p class="font-bold text-lg text-foreground mt-6 mb-2 leading-relaxed">${line}</p>`;
                              }
                              // Numbered items (1., 2., etc) - make bolder
                              else if (line.trim().match(/^\d+\./)) {
                                return `<p class="font-semibold text-base text-foreground mt-3 mb-2 leading-relaxed">${line}</p>`;
                              }
                              // Bullet points - make bolder
                              else if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
                                const content = line.trim().substring(2);
                                return `<p class="ml-4 text-gray-300 font-medium mb-2 leading-relaxed">• ${content}</p>`;
                              }
                              // Regular paragraphs - make bolder and easier to read
                              else if (line.trim()) {
                                return `<p class="text-gray-300 font-medium leading-relaxed mb-3">${line}</p>`;
                              }
                              return '<div class="h-3"></div>'; // Whitespace
                            })
                            .join('') 
                        }}
                      />
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
