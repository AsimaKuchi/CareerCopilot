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
      subtitle: "Tell us what you're looking for.",
      points: [
        "Upload your resume — AI fills in the rest",
        "Set target roles, locations, and preferences",
      ],
      highlight: "Your profile guides every recommendation.",
      color: "indigo",
    },
    {
      number: "02",
      icon: Search,
      title: "Smart Job Matching",
      subtitle: "We find the right roles, not all of them.",
      points: [
        "Scans top job boards for strong-fit roles",
        "Skips bad matches — and tells you why",
      ],
      highlight: "Quality over quantity. Always.",
      color: "emerald",
    },
    {
      number: "03",
      icon: Eye,
      title: "Review & Approve",
      subtitle: "Nothing goes out without your OK.",
      points: [
        "Tailored resume + cover letter for each role",
        "Approve, edit, skip, or save for later",
      ],
      highlight: "You stay in full control.",
      color: "amber",
    },
    {
      number: "04",
      icon: Send,
      title: "One-Click Apply",
      subtitle: "We handle the forms. You make the calls.",
      points: [
        "Auto-fills applications on any job site",
        "Uploads the right documents automatically",
      ],
      highlight: "From job page to submitted in seconds.",
      color: "rose",
    },
    {
      number: "05",
      icon: BarChart3,
      title: "Track & Prepare",
      subtitle: "Every application, one dashboard.",
      points: [
        "Track statuses and follow-up reminders",
        "Interview prep with role-specific insights",
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
            className="flex items-center gap-1 cursor-pointer"
            onClick={() => navigate("/")}
          >
            <div className="relative leading-tight">
              <div className="flex items-center">
                <span className="text-xl font-bold text-gray-900 tracking-tight">MyCareer</span>
                <svg className="w-4 h-4 text-gray-500 ml-0.5 -mt-1 -rotate-45" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M21 16v-2l-8-5V3.5A1.5 1.5 0 0 0 11.5 2A1.5 1.5 0 0 0 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z" />
                </svg>
              </div>
              <div className="flex items-center -mt-1">
                <svg className="w-3 h-4 text-indigo-400 -mr-0.5 flex-shrink-0" viewBox="0 0 12 20" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M11 1C6 1 2 4 2 8C2 12 6 14 6 14" />
                </svg>
                <span className="text-xl font-bold text-indigo-500 tracking-tight">CoPilot</span>
              </div>
            </div>
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
              onClick={() => navigate('/auth')}
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
                    <div className="flex-1 p-6 lg:p-8 space-y-3">
                      <div>
                        <h2 className="text-2xl font-bold text-foreground mb-1">{step.title}</h2>
                        <p className="text-base text-muted-foreground">{step.subtitle}</p>
                      </div>

                      <ul className="space-y-2">
                        {step.points.map((point, j) => (
                          <li key={j} className="flex items-start gap-3">
                            <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                            <span className="text-muted-foreground">{point}</span>
                          </li>
                        ))}
                      </ul>

                      {/* Highlight */}
                      <div className="pt-3">
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
                  onClick={() => navigate('/auth')}
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
            <span className="text-sm text-muted-foreground">© 2025 MyCareerCoPilot. All rights reserved.</span>
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
