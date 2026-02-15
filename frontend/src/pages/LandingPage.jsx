import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Sparkles,
  FileText,
  Target,
  ArrowRight,
  CheckCircle,
  Shield,
  Brain,
  Clock,
  Lock,
  Users,
  FileCheck,
  XCircle,
  Eye,
  AlertTriangle,
  MapPin,
  Zap,
  Chrome,
  MousePointerClick,
  Download,
} from "lucide-react";

// REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
const handleGoogleLogin = () => {
  const redirectUrl = window.location.origin + "/dashboard";
  window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
};

export default function LandingPage() {
  const navigate = useNavigate();
  const [hoveredFeature, setHoveredFeature] = useState(null);

  const features = [
    {
      icon: Chrome,
      title: "One-Click Auto-Fill on Any Job Page",
      description: "Found a job on Greenhouse, Lever, or Ashby? Our Chrome extension auto-fills the entire application in seconds — name, experience, work authorization, everything.",
      highlight: "No more copy-pasting. No more typos.",
      color: "text-indigo-500",
      bgColor: "bg-indigo-50",
    },
    {
      icon: FileText,
      title: "AI-Optimized Resume & Cover Letter",
      description: "The extension doesn't just fill forms — it uploads a resume and cover letter tailored specifically to THAT job, using your profile and the job description.",
      highlight: "Every application is customized. Automatically.",
      color: "text-emerald-500",
      bgColor: "bg-emerald-50",
    },
    {
      icon: MousePointerClick,
      title: "Smart Dropdown Handling",
      description: "Those tricky dropdown menus? We handle them. Work authorization, experience level, start date — the extension intelligently selects the right options for you.",
      highlight: "Even the annoying fields get filled correctly.",
      color: "text-amber-500",
      bgColor: "bg-amber-50",
    },
    {
      icon: Target,
      title: "Track Every Application Automatically",
      description: "When you hit submit, the extension logs it instantly to your dashboard. No spreadsheets needed. Follow-up reminders, interview prep, and next steps — all in one place.",
      highlight: "Apply on their site. Track on yours.",
      color: "text-rose-500",
      bgColor: "bg-rose-50",
    },
  ];

  const trustBadges = [
    { icon: Shield, label: "256-bit SSL Encryption" },
    { icon: MapPin, label: "PIPEDA-Compliant" },
    { icon: Users, label: "Human-in-the-Loop System" },
    { icon: XCircle, label: "No Blind Auto-Apply" },
  ];

  const skipReasons = [
    "Skip low-fit roles",
    "Flag stretch opportunities",
    "Explain risk vs reward",
    "Let you decide when to proceed",
  ];

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Background Elements */}
      <div className="hero-glow" />
      <div className="noise-overlay fixed inset-0 pointer-events-none" />
      
      {/* Floating Orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-500/5 rounded-full blur-3xl animate-pulse-slow" />
      <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-emerald-500/5 rounded-full blur-3xl animate-pulse-slow" />

      {/* Header */}
      <header className="relative z-10 px-6 py-6">
        <nav className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-foreground">JobMatch AI</span>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              onClick={() => navigate('/how-it-works')}
              className="text-muted-foreground hover:text-foreground hidden sm:inline-flex"
            >
              How It Works
            </Button>
            <Button
              data-testid="header-signin-btn"
              onClick={handleGoogleLogin}
              className="bg-indigo-500 hover:bg-indigo-600 text-white"
            >
              Sign In
            </Button>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <main className="relative z-10 px-6">
        <div className="max-w-5xl mx-auto pt-16 pb-20 text-center">
          <div className="space-y-8 animate-fade-in">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/20">
              <Target className="w-4 h-4 text-indigo-500" />
              <span className="text-sm text-indigo-600 font-medium">Quality-First Job Applications</span>
            </div>
            
            {/* Main Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight text-foreground">
              Apply to the right jobs —{" "}
              <span className="text-gradient">not every job</span>
            </h1>
            
            {/* Subheadline */}
            <p className="text-lg sm:text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
              A quality-first job application platform that finds strong matches, explains why they fit, 
              and lets you approve every application before it's sent.
            </p>

            {/* Anti-spam message */}
            <p className="text-base text-foreground font-medium">
              No resume spam. No blind auto-apply. No burned opportunities.
            </p>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-4">
              <Button
                data-testid="get-started-btn"
                onClick={handleGoogleLogin}
                size="lg"
                className="bg-indigo-500 hover:bg-indigo-600 text-white btn-glow group h-14 px-8 text-base"
              >
                Find jobs that actually fit me
                <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
              </Button>
              <Button
                data-testid="learn-more-btn"
                variant="link"
                size="lg"
                className="text-indigo-600 hover:text-indigo-700 h-14 px-4 text-base"
                onClick={() => navigate('/how-it-works')}
              >
                See how it works →
              </Button>
            </div>
          </div>
        </div>

        {/* Credibility Metrics */}
        <section className="max-w-5xl mx-auto pb-20">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="glass-light text-center p-6 shadow-sm">
              <CardContent className="p-0">
                <div className="flex justify-center mb-2">
                  <Clock className="w-6 h-6 text-indigo-500" />
                </div>
                <p className="text-2xl font-bold text-foreground">25+ min</p>
                <p className="text-sm text-muted-foreground mt-1">Average time saved per application</p>
              </CardContent>
            </Card>
            <Card className="glass-light text-center p-6 shadow-sm">
              <CardContent className="p-0">
                <div className="flex justify-center mb-2">
                  <Zap className="w-6 h-6 text-amber-500" />
                </div>
                <p className="text-2xl font-bold text-foreground">3–5x faster</p>
                <p className="text-sm text-muted-foreground mt-1">From job page → ready to submit</p>
              </CardContent>
            </Card>
            <Card className="glass-light text-center p-6 shadow-sm">
              <CardContent className="p-0">
                <div className="flex justify-center mb-2">
                  <Target className="w-6 h-6 text-emerald-500" />
                </div>
                <p className="text-2xl font-bold text-foreground">Quality-first</p>
                <p className="text-sm text-muted-foreground mt-1">Strong-fit roles only — no resume spam</p>
              </CardContent>
            </Card>
            <Card className="glass-light text-center p-6 shadow-sm">
              <CardContent className="p-0">
                <div className="flex justify-center mb-2">
                  <Shield className="w-6 h-6 text-blue-500" />
                </div>
                <p className="text-2xl font-bold text-foreground">100% human</p>
                <p className="text-sm text-muted-foreground mt-1">You approve every submission</p>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Why Choose Us Section */}
        <section id="how-it-works" className="max-w-6xl mx-auto py-20">
          <div className="text-center mb-16 animate-fade-in">
            <h2 className="text-3xl lg:text-4xl font-bold text-foreground mb-4">
              Why choose a quality-first approach?
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Most job tools optimize for volume.{" "}
              <span className="text-foreground font-semibold">We optimize for interviews.</span>
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {features.map((feature, i) => (
              <Card
                key={i}
                data-testid={`feature-card-${i}`}
                className={`glass-light rounded-xl card-hover cursor-pointer shadow-sm ${
                  hoveredFeature === i ? 'border-indigo-500/30' : ''
                }`}
                onMouseEnter={() => setHoveredFeature(i)}
                onMouseLeave={() => setHoveredFeature(null)}
              >
                <CardContent className="p-8 space-y-4">
                  <div className={`w-14 h-14 rounded-xl ${feature.bgColor} flex items-center justify-center ${feature.color}`}>
                    <feature.icon className="w-7 h-7" />
                  </div>
                  <h3 className="text-xl font-semibold text-foreground">{feature.title}</h3>
                  <p className="text-muted-foreground leading-relaxed">{feature.description}</p>
                  <p className="text-sm font-medium text-foreground pt-2 border-t border-gray-100">
                    {feature.highlight}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* Testimonials Section */}
        <section className="max-w-6xl mx-auto py-20">
          <div className="text-center mb-12">
            <h2 className="text-3xl lg:text-4xl font-bold text-foreground mb-4">
              What our users are saying
            </h2>
            <p className="text-lg text-muted-foreground">
              Real results from real job seekers across Canada
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {/* Review 1 */}
            <Card className="glass-light rounded-xl shadow-sm" data-testid="review-1">
              <CardContent className="p-6 space-y-4">
                <div className="flex gap-1">
                  {[...Array(5)].map((_, i) => (
                    <svg key={i} className="w-5 h-5 text-amber-400 fill-current" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  ))}
                </div>
                <p className="text-foreground leading-relaxed italic">
                  "I went from spending 3 hours daily on applications to just 15 minutes. Landed 4 interviews in my first week!"
                </p>
                <div className="pt-4 border-t border-gray-100">
                  <p className="font-semibold text-foreground">Sarah Chen</p>
                  <p className="text-sm text-muted-foreground">Software Developer • Toronto, ON</p>
                </div>
              </CardContent>
            </Card>

            {/* Review 2 */}
            <Card className="glass-light rounded-xl shadow-sm" data-testid="review-2">
              <CardContent className="p-6 space-y-4">
                <div className="flex gap-1">
                  {[...Array(5)].map((_, i) => (
                    <svg key={i} className="w-5 h-5 text-amber-400 fill-current" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  ))}
                </div>
                <p className="text-foreground leading-relaxed italic">
                  "The AI matching is incredible. Every job suggestion was spot-on for my experience level and career goals."
                </p>
                <div className="pt-4 border-t border-gray-100">
                  <p className="font-semibold text-foreground">Marcus Miller</p>
                  <p className="text-sm text-muted-foreground">Marketing Manager • Ottawa, ON</p>
                </div>
              </CardContent>
            </Card>

            {/* Review 3 */}
            <Card className="glass-light rounded-xl shadow-sm" data-testid="review-3">
              <CardContent className="p-6 space-y-4">
                <div className="flex gap-1">
                  {[...Array(5)].map((_, i) => (
                    <svg key={i} className="w-5 h-5 text-amber-400 fill-current" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  ))}
                </div>
                <p className="text-foreground leading-relaxed italic">
                  "As a new immigrant, this tool was a lifesaver. It understood the Canadian job market perfectly."
                </p>
                <div className="pt-4 border-t border-gray-100">
                  <p className="font-semibold text-foreground">Priya Sharma</p>
                  <p className="text-sm text-muted-foreground">Data Analyst • Mississauga, ON</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Why We Skip Jobs Section */}
        <section className="max-w-4xl mx-auto py-20">
          <Card className="glass-heavy rounded-2xl overflow-hidden relative shadow-xl">
            <div className="absolute inset-0 bg-gradient-to-r from-amber-500/5 to-rose-500/5" />
            <CardContent className="relative p-10 md:p-12">
              <div className="flex items-start gap-4 mb-6">
                <div className="w-12 h-12 rounded-xl bg-amber-100 flex items-center justify-center flex-shrink-0">
                  <AlertTriangle className="w-6 h-6 text-amber-600" />
                </div>
                <div>
                  <h2 className="text-2xl lg:text-3xl font-bold text-foreground mb-2">
                    Why We Skip Jobs On Purpose
                  </h2>
                  <p className="text-muted-foreground">
                    Applying to the wrong job can hurt your chances at a company forever.
                  </p>
                </div>
              </div>
              
              <p className="text-foreground mb-6">That's why we:</p>
              
              <div className="grid sm:grid-cols-2 gap-3 mb-8">
                {skipReasons.map((reason, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-white/50">
                    <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                    <span className="text-foreground">{reason}</span>
                  </div>
                ))}
              </div>

              <p className="text-lg font-semibold text-foreground text-center pt-4 border-t border-gray-200">
                Skipping is not failure — it's strategy.
              </p>
            </CardContent>
          </Card>
        </section>

        {/* Trust Badges Section */}
        <section className="max-w-5xl mx-auto py-16">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {trustBadges.map((badge, i) => (
              <div key={i} className="flex flex-col items-center text-center p-4">
                <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mb-3">
                  <badge.icon className="w-6 h-6 text-gray-600" />
                </div>
                <p className="text-sm font-medium text-foreground">{badge.label}</p>
              </div>
            ))}
          </div>
          <p className="text-center text-sm text-muted-foreground mt-6">
            Built for candidates who care about long-term career outcomes.
          </p>
        </section>

        {/* Final CTA Section */}
        <section className="max-w-4xl mx-auto py-20">
          <Card className="glass-heavy rounded-2xl overflow-hidden relative shadow-xl">
            <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/5 to-emerald-500/5" />
            <CardContent className="relative p-12 text-center space-y-6">
              <h2 className="text-3xl lg:text-4xl font-bold text-foreground">
                Stop applying blindly.
              </h2>
              <p className="text-2xl text-foreground font-medium">
                Start applying intentionally.
              </p>
              <p className="text-lg text-muted-foreground max-w-xl mx-auto">
                Review fewer jobs. Send better applications. Get more interviews.
              </p>
              <Button
                data-testid="cta-get-started-btn"
                onClick={handleGoogleLogin}
                size="lg"
                className="bg-indigo-500 hover:bg-indigo-600 text-white btn-glow h-14 px-10 text-base mt-4"
              >
                Find jobs that actually fit me
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
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
            <span className="text-sm text-muted-foreground">© 2025 JobMatch AI. All rights reserved.</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Privacy</a>
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Terms</a>
            <Link to="/support" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Support</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
