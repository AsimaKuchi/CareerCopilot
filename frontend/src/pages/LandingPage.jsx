import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Sparkles,
  FileText,
  Target,
  MessageSquare,
  ArrowRight,
  CheckCircle,
  Zap,
  Shield,
  TrendingUp,
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
      icon: Target,
      title: "AI Job Matching",
      description: "Smart algorithms analyze your profile to find jobs that match your skills and preferences.",
      color: "text-indigo-400",
    },
    {
      icon: FileText,
      title: "ATS Resume Optimizer",
      description: "Automatically optimize your resume for each job to pass ATS screening systems.",
      color: "text-emerald-400",
    },
    {
      icon: MessageSquare,
      title: "Cover Letter Generator",
      description: "AI-crafted personalized cover letters tailored to each position you apply for.",
      color: "text-amber-400",
    },
    {
      icon: Zap,
      title: "One-Click Apply",
      description: "Review and approve applications with optimized materials in a single click.",
      color: "text-rose-400",
    },
  ];

  const benefits = [
    "Save 10+ hours per week on applications",
    "3x higher response rate from employers",
    "AI-powered interview preparation",
    "Track all applications in one place",
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
          <Button
            data-testid="header-signin-btn"
            onClick={handleGoogleLogin}
            className="bg-indigo-500 hover:bg-indigo-600 text-white"
          >
            Sign In
          </Button>
        </nav>
      </header>

      {/* Hero Section */}
      <main className="relative z-10 px-6">
        <div className="max-w-7xl mx-auto pt-20 pb-32">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            {/* Left Column - Text */}
            <div className="space-y-8 animate-fade-in">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/20">
                <Sparkles className="w-4 h-4 text-indigo-500" />
                <span className="text-sm text-indigo-600 font-medium">AI-Powered Job Search</span>
              </div>
              
              <h1 className="text-5xl lg:text-6xl font-bold leading-tight">
                <span className="text-gradient">Land Your Dream Job</span>
                <br />
                <span className="text-foreground">With AI Assistance</span>
              </h1>
              
              <p className="text-lg text-muted-foreground max-w-xl leading-relaxed">
                Stop spending hours on applications. Our AI finds the perfect jobs, 
                optimizes your resume, writes cover letters, and prepares you for interviews.
              </p>

              <div className="flex flex-col sm:flex-row gap-4">
                <Button
                  data-testid="get-started-btn"
                  onClick={handleGoogleLogin}
                  size="lg"
                  className="bg-indigo-500 hover:bg-indigo-600 text-white btn-glow group h-12 px-8"
                >
                  Get Started Free
                  <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                </Button>
                <Button
                  data-testid="learn-more-btn"
                  variant="outline"
                  size="lg"
                  className="border-gray-300 hover:bg-gray-50 h-12 px-8"
                  onClick={() => document.getElementById('features').scrollIntoView({ behavior: 'smooth' })}
                >
                  Learn More
                </Button>
              </div>

              {/* Benefits List */}
              <div className="grid grid-cols-2 gap-3 pt-4">
                {benefits.map((benefit, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm text-muted-foreground">
                    <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                    <span>{benefit}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Right Column - Visual */}
            <div className="relative animate-fade-in-delay-2 hidden lg:block">
              <div className="relative">
                {/* Main Card */}
                <Card className="glass-heavy rounded-2xl overflow-hidden shadow-xl">
                  <CardContent className="p-0">
                    <img
                      src="https://images.unsplash.com/photo-1750969185331-e03829f72c7d?crop=entropy&cs=srgb&fm=jpg&q=85&w=800"
                      alt="AI Network"
                      className="w-full h-80 object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-white via-transparent to-transparent" />
                  </CardContent>
                </Card>

                {/* Floating Stats Cards */}
                <div className="absolute -left-8 top-1/4 glass-heavy rounded-xl p-4 animate-fade-in-delay-3 shadow-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                      <TrendingUp className="w-5 h-5 text-emerald-500" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-foreground">92%</p>
                      <p className="text-xs text-muted-foreground">Match Rate</p>
                    </div>
                  </div>
                </div>

                <div className="absolute -right-4 bottom-1/4 glass-heavy rounded-xl p-4 animate-fade-in-delay-3 shadow-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-indigo-500/20 flex items-center justify-center">
                      <Shield className="w-5 h-5 text-indigo-500" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-foreground">ATS</p>
                      <p className="text-xs text-muted-foreground">Optimized</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <section id="features" className="max-w-7xl mx-auto py-24">
          <div className="text-center mb-16 animate-fade-in">
            <h2 className="text-3xl lg:text-4xl font-bold text-foreground mb-4">
              Everything You Need to Succeed
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Our AI-powered platform handles every aspect of your job search, 
              from finding opportunities to preparing for interviews.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, i) => (
              <Card
                key={i}
                data-testid={`feature-card-${i}`}
                className={`glass-light rounded-xl card-hover cursor-pointer ${
                  hoveredFeature === i ? 'border-indigo-500/30' : ''
                }`}
                onMouseEnter={() => setHoveredFeature(i)}
                onMouseLeave={() => setHoveredFeature(null)}
              >
                <CardContent className="p-6 space-y-4">
                  <div className={`w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center ${feature.color}`}>
                    <feature.icon className="w-6 h-6" />
                  </div>
                  <h3 className="text-lg font-semibold text-foreground">{feature.title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* CTA Section */}
        <section className="max-w-4xl mx-auto py-24">
          <Card className="glass-heavy rounded-2xl overflow-hidden relative">
            <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/10 to-emerald-500/10" />
            <CardContent className="relative p-12 text-center space-y-6">
              <h2 className="text-3xl lg:text-4xl font-bold text-foreground">
                Ready to Transform Your Job Search?
              </h2>
              <p className="text-muted-foreground max-w-xl mx-auto">
                Join thousands of job seekers who have already landed their dream jobs 
                using JobMatch AI.
              </p>
              <Button
                data-testid="cta-get-started-btn"
                onClick={handleGoogleLogin}
                size="lg"
                className="bg-indigo-500 hover:bg-indigo-600 text-white btn-glow h-12 px-8"
              >
                Start Free Today
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </CardContent>
          </Card>
        </section>
      </main>

      {/* Footer */}
      <footer className="relative z-10 px-6 py-8 border-t border-white/5">
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
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
