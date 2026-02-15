import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Sparkles,
  User,
  Search,
  Eye,
  Send,
  BarChart3,
  ArrowRight,
  CheckCircle,
  XCircle,
  FileText,
  MapPin,
  Briefcase,
  Shield,
  AlertTriangle,
  Clock,
  Target,
  Settings,
  FileCheck,
  Edit,
  Bookmark,
  LayoutDashboard,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

// REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
const handleGoogleLogin = () => {
  const redirectUrl = window.location.origin + "/dashboard";
  window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
};

export default function HowItWorks() {
  const navigate = useNavigate();

  const steps = [
    {
      number: "01",
      icon: User,
      title: "Build Your Profile",
      subtitle: "Tell us what good looks like for you.",
      description: "Upload your resume and set your preferences so we understand:",
      points: [
        "Your target roles and experience level",
        "Preferred locations (Toronto, GTA, Ontario, Remote, etc.)",
        "Industries you want to focus on",
        "Work authorization and work arrangement preferences",
      ],
      highlight: "Your profile guides every recommendation — nothing is guessed.",
      color: "indigo",
    },
    {
      number: "02",
      icon: Search,
      title: "Job Matching (With Explanations)",
      subtitle: "We don't apply everywhere. We match carefully.",
      description: "Our system scans supported job boards (starting with Greenhouse) and evaluates roles based on:",
      points: [
        "Role relevance",
        "Experience fit",
        "Location alignment",
        "Industry match",
        "Your application intensity (conservative → ambitious)",
      ],
      extras: [
        { icon: CheckCircle, text: "Jobs we recommend", color: "text-emerald-500" },
        { icon: XCircle, text: "Jobs we skip — and why", color: "text-rose-500" },
        { icon: Target, text: "Clear reasoning behind every match", color: "text-indigo-500" },
      ],
      highlight: "Skipping is intentional. It protects your long-term chances.",
      color: "emerald",
    },
    {
      number: "03",
      icon: Eye,
      title: "Review Before Applying",
      subtitle: "Nothing is submitted without your approval.",
      description: "For each recommended role, we prepare:",
      points: [
        "A tailored resume version",
        "A role-specific cover letter",
        "A preview of the application flow",
      ],
      actions: [
        { icon: CheckCircle, text: "Approve", color: "text-emerald-500" },
        { icon: Edit, text: "Edit", color: "text-amber-500" },
        { icon: XCircle, text: "Skip", color: "text-rose-500" },
        { icon: Bookmark, text: "Save for later", color: "text-indigo-500" },
      ],
      highlight: "This keeps quality high and avoids résumé spam.",
      color: "amber",
    },
    {
      number: "04",
      icon: Send,
      title: "Apply With Confidence",
      subtitle: "When you approve, we handle the technical steps — not the decisions.",
      description: "We assist with:",
      points: [
        "Form filling on supported platforms",
        "Uploading the correct documents",
        "Ensuring applications are submitted correctly",
      ],
      tracking: [
        "Where you applied",
        "What was sent",
        "When it was submitted",
      ],
      highlight: "Everything is tracked in your dashboard.",
      color: "rose",
    },
    {
      number: "05",
      icon: BarChart3,
      title: "Track & Prepare",
      subtitle: "Applying is just the start.",
      description: "From your dashboard, you can:",
      points: [
        "Track application statuses",
        "See which roles are gaining traction",
        "Prepare for interviews with role-specific insights",
      ],
      highlight: "The goal isn't more applications — it's more interviews.",
      color: "purple",
    },
  ];

  const autoApplyProblems = [
    "Get you rejected faster",
    "Lock you out of companies",
    "Flood ATS systems with low-signal applications",
  ];

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Background Elements */}
      <div className="hero-glow" />
      <div className="noise-overlay fixed inset-0 pointer-events-none" />

      {/* Header */}
      <header className="relative z-10 px-6 py-6">
        <nav className="max-w-7xl mx-auto flex items-center justify-between">
          <div 
            className="flex items-center gap-2 cursor-pointer"
            onClick={() => navigate("/")}
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-foreground">CareerCopilot AI</span>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              onClick={() => navigate("/")}
              className="border-gray-300 hover:bg-gray-50"
              data-testid="home-btn"
            >
              ← Back to Home
            </Button>
            <Button
              data-testid="header-signin-btn"
              onClick={handleGoogleLogin}
              className="bg-indigo-500 hover:bg-indigo-600 text-white"
            >
              Get Started
            </Button>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <main className="relative z-10 px-6">
        <div className="max-w-4xl mx-auto pt-16 pb-12 text-center">
          <div className="space-y-6 animate-fade-in">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/20">
              <Settings className="w-4 h-4 text-indigo-500" />
              <span className="text-sm text-indigo-600 font-medium">How It Works</span>
            </div>
            
            <h1 className="text-4xl sm:text-5xl font-bold leading-tight text-foreground">
              A smarter way to apply —{" "}
              <span className="text-gradient">without burning opportunities</span>
            </h1>
            
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              Our platform helps you find the right jobs, prepare high-quality applications, 
              and apply with confidence — all with you in control.
            </p>
          </div>
        </div>

        {/* Steps Section */}
        <section className="max-w-5xl mx-auto py-12">
          <div className="space-y-8">
            {steps.map((step, i) => (
              <Card 
                key={i} 
                className="glass-light rounded-2xl overflow-hidden shadow-sm"
                data-testid={`step-${i + 1}`}
              >
                <CardContent className="p-0">
                  <div className="flex flex-col lg:flex-row">
                    {/* Step Number */}
                    <div className={`lg:w-32 p-6 lg:p-8 flex lg:flex-col items-center lg:items-start gap-4 lg:gap-2 bg-${step.color}-50 border-b lg:border-b-0 lg:border-r border-gray-100`}>
                      <span className={`text-4xl lg:text-5xl font-bold text-${step.color}-500 opacity-50`}>
                        {step.number}
                      </span>
                      <div className={`w-12 h-12 rounded-xl bg-${step.color}-100 flex items-center justify-center`}>
                        <step.icon className={`w-6 h-6 text-${step.color}-500`} />
                      </div>
                    </div>

                    {/* Step Content */}
                    <div className="flex-1 p-6 lg:p-8 space-y-4">
                      <div>
                        <h2 className="text-2xl font-bold text-foreground mb-1">{step.title}</h2>
                        <p className="text-lg text-muted-foreground">{step.subtitle}</p>
                      </div>

                      <p className="text-foreground">{step.description}</p>

                      <ul className="space-y-2">
                        {step.points.map((point, j) => (
                          <li key={j} className="flex items-start gap-3">
                            <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                            <span className="text-muted-foreground">{point}</span>
                          </li>
                        ))}
                      </ul>

                      {/* Extras for Step 2 */}
                      {step.extras && (
                        <div className="pt-4 border-t border-gray-100">
                          <p className="text-foreground font-medium mb-3">You'll see:</p>
                          <div className="grid sm:grid-cols-3 gap-3">
                            {step.extras.map((extra, j) => (
                              <div key={j} className="flex items-center gap-2 p-3 rounded-lg bg-gray-50">
                                <extra.icon className={`w-5 h-5 ${extra.color}`} />
                                <span className="text-sm text-foreground">{extra.text}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Actions for Step 3 */}
                      {step.actions && (
                        <div className="pt-4 border-t border-gray-100">
                          <p className="text-foreground font-medium mb-3">You choose what to:</p>
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                            {step.actions.map((action, j) => (
                              <div key={j} className="flex items-center gap-2 p-3 rounded-lg bg-gray-50">
                                <action.icon className={`w-5 h-5 ${action.color}`} />
                                <span className="text-sm text-foreground">{action.text}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Tracking for Step 4 */}
                      {step.tracking && (
                        <div className="pt-4 border-t border-gray-100">
                          <p className="text-foreground font-medium mb-3">You always know:</p>
                          <div className="grid sm:grid-cols-3 gap-3">
                            {step.tracking.map((item, j) => (
                              <div key={j} className="flex items-center gap-2 p-3 rounded-lg bg-gray-50">
                                <FileCheck className="w-5 h-5 text-indigo-500" />
                                <span className="text-sm text-foreground">{item}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Highlight */}
                      <div className="pt-4">
                        <p className="text-foreground font-semibold flex items-center gap-2">
                          <Sparkles className="w-4 h-4 text-indigo-500" />
                          {step.highlight}
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* Why We're Not Auto-Apply Section */}
        <section className="max-w-4xl mx-auto py-16">
          <Card className="glass-heavy rounded-2xl overflow-hidden relative shadow-xl">
            <div className="absolute inset-0 bg-gradient-to-r from-rose-500/5 to-amber-500/5" />
            <CardContent className="relative p-10 md:p-12">
              <div className="flex items-start gap-4 mb-8">
                <div className="w-14 h-14 rounded-xl bg-rose-100 flex items-center justify-center flex-shrink-0">
                  <AlertTriangle className="w-7 h-7 text-rose-600" />
                </div>
                <div>
                  <h2 className="text-2xl lg:text-3xl font-bold text-foreground mb-2">
                    Why We're Not "Auto-Apply"
                  </h2>
                  <p className="text-lg text-muted-foreground">
                    Many tools optimize for volume.{" "}
                    <span className="text-foreground font-semibold">We optimize for outcomes.</span>
                  </p>
                </div>
              </div>

              <div className="mb-8">
                <p className="text-foreground mb-4">Auto-applying everywhere can:</p>
                <div className="space-y-3">
                  {autoApplyProblems.map((problem, i) => (
                    <div key={i} className="flex items-center gap-3 p-4 rounded-lg bg-rose-50 border border-rose-100">
                      <XCircle className="w-5 h-5 text-rose-500 flex-shrink-0" />
                      <span className="text-foreground">{problem}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="text-center pt-6 border-t border-gray-200">
                <p className="text-xl font-semibold text-foreground">
                  That's why every application here is{" "}
                  <span className="text-indigo-600">intentional</span>.
                </p>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Final CTA Section */}
        <section className="max-w-4xl mx-auto py-16">
          <Card className="glass-heavy rounded-2xl overflow-hidden relative shadow-xl">
            <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/5 to-emerald-500/5" />
            <CardContent className="relative p-12 text-center space-y-6">
              <h2 className="text-3xl lg:text-4xl font-bold text-foreground">
                Ready to apply smarter?
              </h2>
              <p className="text-lg text-muted-foreground max-w-xl mx-auto">
                Join thousands of candidates who care about quality over quantity.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
                <Button
                  data-testid="cta-get-started-btn"
                  onClick={handleGoogleLogin}
                  size="lg"
                  className="bg-indigo-500 hover:bg-indigo-600 text-white btn-glow h-14 px-10 text-base"
                >
                  Find jobs that actually fit me
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
                <Button
                  variant="outline"
                  size="lg"
                  onClick={() => navigate("/")}
                  className="h-14 px-8 text-base border-gray-300"
                >
                  Back to Home
                </Button>
              </div>
            </CardContent>
          </Card>
        </section>
      </main>

      {/* Footer */}
      <footer className="relative z-10 px-6 py-8 border-t border-gray-200">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="text-sm text-muted-foreground">© 2025 CareerCopilot AI. All rights reserved.</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Privacy</a>
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Terms</a>
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
