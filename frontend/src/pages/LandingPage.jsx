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
            <span className="text-xl font-bold text-foreground">CareerCopilot AI</span>
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
              onClick={() => navigate('/auth')}
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
                onClick={() => navigate('/auth')}
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

        {/* Company Logo Carousel */}
        <section className="max-w-6xl mx-auto pb-16 overflow-hidden">
          <p className="text-center text-sm text-muted-foreground mb-8">
            Works with applications at top companies
          </p>
          <div className="relative">
            {/* Gradient fade edges */}
            <div className="absolute left-0 top-0 bottom-0 w-20 bg-gradient-to-r from-background to-transparent z-10"></div>
            <div className="absolute right-0 top-0 bottom-0 w-20 bg-gradient-to-l from-background to-transparent z-10"></div>
            
            {/* Scrolling container */}
            <div className="flex animate-scroll">
              {/* First set of logos */}
              <div className="flex items-center gap-16 px-8 shrink-0">
                {/* Google */}
                <svg className="h-8 w-auto opacity-70 hover:opacity-100 transition-opacity" viewBox="0 0 272 92">
                  <path fill="#EA4335" d="M115.75 47.18c0 12.77-9.99 22.18-22.25 22.18s-22.25-9.41-22.25-22.18C71.25 34.32 81.24 25 93.5 25s22.25 9.32 22.25 22.18zm-9.74 0c0-7.98-5.79-13.44-12.51-13.44S80.99 39.2 80.99 47.18c0 7.9 5.79 13.44 12.51 13.44s12.51-5.55 12.51-13.44z"/>
                  <path fill="#FBBC05" d="M163.75 47.18c0 12.77-9.99 22.18-22.25 22.18s-22.25-9.41-22.25-22.18c0-12.85 9.99-22.18 22.25-22.18s22.25 9.32 22.25 22.18zm-9.74 0c0-7.98-5.79-13.44-12.51-13.44s-12.51 5.46-12.51 13.44c0 7.9 5.79 13.44 12.51 13.44s12.51-5.55 12.51-13.44z"/>
                  <path fill="#4285F4" d="M209.75 26.34v39.82c0 16.38-9.66 23.07-21.08 23.07-10.75 0-17.22-7.19-19.66-13.07l8.48-3.53c1.51 3.61 5.21 7.87 11.17 7.87 7.31 0 11.84-4.51 11.84-13v-3.19h-.34c-2.18 2.69-6.38 5.04-11.68 5.04-11.09 0-21.25-9.66-21.25-22.09 0-12.52 10.16-22.26 21.25-22.26 5.29 0 9.49 2.35 11.68 4.96h.34v-3.61h9.25zm-8.56 20.92c0-7.81-5.21-13.52-11.84-13.52-6.72 0-12.35 5.71-12.35 13.52 0 7.73 5.63 13.36 12.35 13.36 6.63 0 11.84-5.63 11.84-13.36z"/>
                  <path fill="#34A853" d="M225 3v65h-9.5V3h9.5z"/>
                  <path fill="#EA4335" d="M262.02 54.48l7.56 5.04c-2.44 3.61-8.32 9.83-18.48 9.83-12.6 0-22.01-9.74-22.01-22.18 0-13.19 9.49-22.18 20.92-22.18 11.51 0 17.14 9.16 18.98 14.11l1.01 2.52-29.65 12.28c2.27 4.45 5.8 6.72 10.75 6.72 4.96 0 8.4-2.44 10.92-6.14zm-23.27-7.98l19.82-8.23c-1.09-2.77-4.37-4.7-8.23-4.7-4.95 0-11.84 4.37-11.59 12.93z"/>
                  <path fill="#4285F4" d="M35.29 41.41V32H67c.31 1.64.47 3.58.47 5.68 0 7.06-1.93 15.79-8.15 22.01-6.05 6.3-13.78 9.66-24.02 9.66C16.32 69.35.36 53.89.36 34.91.36 15.93 16.32.47 35.3.47c10.5 0 17.98 4.12 23.6 9.49l-6.64 6.64c-4.03-3.78-9.49-6.72-16.97-6.72-13.86 0-24.7 11.17-24.7 25.03 0 13.86 10.84 25.03 24.7 25.03 8.99 0 14.11-3.61 17.39-6.89 2.66-2.66 4.41-6.46 5.1-11.65l-22.49.01z"/>
                </svg>
                
                {/* Microsoft */}
                <svg className="h-7 w-auto opacity-70 hover:opacity-100 transition-opacity" viewBox="0 0 318 69">
                  <path fill="#737373" d="M99.1 18.9v30.4h-4.7V23.1h-.1l-11.5 26.2h-3.1L68.1 23.1H68v26.2h-4.4V18.9h6.5l10.7 25h.2l11.4-25h6.7zm5.4 5.9h4.3v3.2h.1c1.5-2.5 4-3.7 7.1-3.7 5.6 0 8.3 3.4 8.3 9.1v16h-4.5V34.2c0-4.2-1.7-6.2-5.2-6.2-4 0-5.8 2.4-5.8 7.4v14h-4.3V24.8zm33.6 20.6h-.1v14h-4.5V24.8h4.3v3.5h.1c1.6-2.7 4.4-4 7.6-4 6.2 0 9.6 4.9 9.6 12.1 0 7.2-3.7 12.1-9.9 12.1-3.1 0-5.6-1.3-7.1-3.1zm-.1-8.7c0 5.1 2.4 8.3 6.5 8.3 4.2 0 6.5-3.4 6.5-8.6 0-5.1-2.2-8.4-6.4-8.4-4.3 0-6.6 3.4-6.6 8.7zm24.3-11.9h4.5v3.7h.1c1.3-2.8 3.8-4.2 7-4.2.9 0 1.5.1 2.2.2v4.3c-.8-.2-1.5-.3-2.4-.3-4.6 0-7 2.9-7 7.8v13h-4.5V24.8h.1zm17.8 12.1c0 5 2.5 8.2 6.8 8.2 3.2 0 5.2-1.7 5.9-4.7h4.6c-1 5.3-4.8 8.4-10.6 8.4-7.2 0-11.3-4.9-11.3-12.1 0-6.9 4.2-12.1 11.2-12.1 7.2 0 11.1 5.4 10.7 12.4h-17.3v-.1zm12.7-3.2c-.3-4.2-2.6-6.7-6.2-6.7-3.7 0-6.1 2.7-6.5 6.7h12.7zm8.4-5.9c0-6.1 4.3-9.7 11.4-10l9.3-.5v-2.6c0-4.4-2.4-6.4-6.6-6.4-3.7 0-6.1 1.6-6.5 4.7h-4.7c.4-5.3 4.8-8.6 11.4-8.6 7 0 11 3.5 11 9.7v21.3h-4.3v-4h-.1c-1.7 3-5 4.5-8.9 4.5-5.4.1-9-3.3-9-8.1zm20.6-2.6v-3l-8.7.5c-4.4.3-6.6 1.9-6.6 5 0 3 2.3 4.9 5.9 4.9 4.8.1 9.4-2.8 9.4-7.4zm11.1-10.4h4.5v3.7h.1c1.3-2.8 3.8-4.2 7-4.2.9 0 1.5.1 2.2.2v4.3c-.8-.2-1.5-.3-2.4-.3-4.6 0-7 2.9-7 7.8v13h-4.5V24.8h.1zm35.3 7.4h-4.6c-.4-3-2.6-4.7-6.3-4.7-3.4 0-5.8 1.4-5.8 3.8 0 2.1 1.5 3.2 4.9 4l4 .8c5.8 1.2 8.3 3.6 8.3 7.7 0 5.2-4.7 8.5-11.1 8.5-6.8 0-11.4-3.2-11.8-8.8h4.7c.5 3.3 3 5 7.2 5 3.9 0 6.4-1.6 6.4-4.1 0-2.2-1.4-3.4-5-4.2l-4.3-1c-5.4-1.2-7.8-3.8-7.8-7.9 0-5 4.4-8.3 10.6-8.3 6.3.1 10.3 3.4 10.6 9.2zm5.3 4.7c0-7 4.2-12.1 10.8-12.1 6.7 0 10.8 5.1 10.8 12.1 0 7.1-4.1 12.1-10.8 12.1-6.7.1-10.8-5-10.8-12.1zm17 0c0-5.1-2.4-8.4-6.3-8.4-3.9 0-6.2 3.3-6.2 8.4s2.4 8.4 6.3 8.4 6.2-3.4 6.2-8.4zm14.2-12.1v-6.1h4.5v6.1h5.4v3.7h-5.4v13.9c0 2.4.9 3.4 3.3 3.4h2.1v3.6c-1.2.2-2.3.3-3.6.3-4.9 0-6.3-2-6.3-6.5V28.5h-4v-3.7h4z"/>
                  <path fill="#F25022" d="M0 0h32.7v32.7H0z"/>
                  <path fill="#7FBA00" d="M36.4 0h32.7v32.7H36.4z"/>
                  <path fill="#00A4EF" d="M0 36.4h32.7v32.7H0z"/>
                  <path fill="#FFB900" d="M36.4 36.4h32.7v32.7H36.4z"/>
                </svg>
                
                {/* Amazon */}
                <svg className="h-7 w-auto opacity-70 hover:opacity-100 transition-opacity" viewBox="0 0 603 182">
                  <path fill="#FF9900" d="M374.1 142.1c-34.5 25.5-84.6 39-127.7 39-60.5 0-114.9-22.4-156.1-59.6-3.2-2.9-.3-6.9 3.6-4.6 44.5 25.9 99.4 41.4 156.2 41.4 38.3 0 80.4-7.9 119.2-24.4 5.8-2.5 10.7 3.8 4.8 8.2z"/>
                  <path fill="#FF9900" d="M387.9 126.5c-4.4-5.6-29.1-2.7-40.2-1.3-3.4.4-3.9-2.5-.9-4.7 19.7-13.8 52-9.8 55.8-5.2 3.8 4.7-1 37.1-19.5 52.6-2.8 2.4-5.5 1.1-4.3-2 4.2-10.4 13.5-33.8 9.1-39.4z"/>
                  <path fill="#232F3E" d="M348.5 21.2V6.4c0-2.2 1.7-3.7 3.7-3.7h65.6c2.1 0 3.8 1.5 3.8 3.7v12.7c0 2.1-1.8 4.9-5 9.3l-34 48.6c12.6-.3 26 1.6 37.4 8 2.6 1.5 3.3 3.6 3.5 5.8v15.8c0 2.2-2.4 4.7-4.9 3.4-20.5-10.8-47.8-12-70.5.1-2.3 1.2-4.7-1.3-4.7-3.5V91.3c0-2.4 0-6.6 2.5-10.3l39.4-56.5h-34.3c-2.1 0-3.8-1.5-3.8-3.7l.3.4zM124.4 109.2h-20c-1.9-.1-3.4-1.6-3.6-3.4V6.7c0-2.1 1.7-3.7 3.8-3.7h18.6c1.9.1 3.5 1.6 3.6 3.5v12.9h.4c4.8-12.6 13.9-18.5 26.2-18.5 12.5 0 20.3 5.9 25.9 18.5 4.8-12.6 15.7-18.5 27.4-18.5 8.3 0 17.4 3.4 23 11.1 6.3 8.5 5 20.9 5 31.8v62c0 2.1-1.7 3.7-3.8 3.7h-19.9c-2-.1-3.6-1.7-3.6-3.7V54.3c0-4.3.4-14.9-.6-18.9-1.5-6.7-6-8.6-11.9-8.6-4.9 0-10 3.3-12.1 8.5-2.1 5.3-1.9 14-1.9 19v51.4c0 2.1-1.7 3.7-3.8 3.7h-19.9c-2-.1-3.6-1.7-3.6-3.7l-.1-51.4c0-11.3 1.9-28-12.4-28-14.5 0-13.9 16.3-13.9 28v51.4c0 2.1-1.7 3.7-3.8 3.7h.1zm311.5-85.3c-14.7 0-15.6 20-15.6 32.5s-.2 39.2 15.4 39.2c15.5 0 16.2-21.5 16.2-34.7 0-8.6-.4-18.9-2.6-27.2-1.9-7.2-5.8-9.8-13.4-9.8zm-.2-24c29.5 0 45.5 25.3 45.5 57.5 0 31.1-17.7 55.8-45.5 55.8-29.2 0-45.1-25.3-45.1-56.9 0-31.8 16.1-56.4 45.1-56.4zM546.9 109.2h-19.8c-2-.1-3.6-1.7-3.6-3.7l-.1-99.1c.2-1.9 1.8-3.4 3.8-3.4h18.5c1.7.1 3.2 1.4 3.5 3v15.2h.4c5.5-13.7 13.2-20.2 26.8-20.2 8.9 0 17.5 3.2 23.1 12 5.2 8.2 5.2 21.9 5.2 31.8v61.1c-.2 1.9-1.9 3.3-3.8 3.3h-20c-1.8-.1-3.3-1.5-3.5-3.3V53.2c0-11.2 1.3-27.5-12.6-27.5-4.9 0-9.4 3.3-11.6 8.3-2.8 6.3-3.2 12.6-3.2 19.2v52.5c0 2.1-1.8 3.7-3.9 3.7l-.2-.2zm-243.7-51c0 7.7.2 14.2-3.7 21.1-3.2 5.6-8.2 9-13.8 9-7.7 0-12.2-5.8-12.2-14.5 0-17 15.3-20.1 29.7-20.1v4.5zm20.2 48.7c-1.3 1.2-3.2 1.3-4.7.5-6.6-5.5-7.8-8-11.4-13.2-10.9 11.1-18.6 14.5-32.8 14.5-16.7 0-29.8-10.3-29.8-31 0-16.1 8.7-27.1 21.2-32.5 10.8-4.8 25.9-5.6 37.5-7v-2.6c0-4.8.4-10.4-2.4-14.5-2.5-3.7-7.2-5.2-11.4-5.2-7.8 0-14.7 4-16.4 12.2-.3 1.8-1.7 3.7-3.6 3.8l-19.3-2.1c-1.7-.4-3.6-1.8-3.1-4.4C252.7 5.9 272.6 0 290.4 0c9.1 0 21.1 2.4 28.3 9.3 9.1 8.5 8.2 19.8 8.2 32.2v29.1c0 8.8 3.6 12.6 7 17.3 1.2 1.7 1.5 3.7-.1 4.9-3.9 3.3-10.9 9.4-14.8 12.8l-.1-.3-.2.6z"/>
                </svg>
                
                {/* Meta */}
                <svg className="h-7 w-auto opacity-70 hover:opacity-100 transition-opacity" viewBox="0 0 512 105">
                  <path fill="#0668E1" d="M471.5 23.4c6.5 0 11.8-5.3 11.8-11.7C483.3 5.3 478 0 471.5 0s-11.8 5.3-11.8 11.7c0 6.5 5.3 11.7 11.8 11.7zm-17.7 79V32h35.5v70.3h-35.5zM390.8 1.5h35.5v39.7h-.7c4.8-6.2 13.5-11.2 26.2-11.2 22.6 0 36.3 17.5 36.3 42.2 0 27.5-16.1 44-38.7 44-12 0-21-5.2-25.8-13h-.5v11h-32.3V1.5zm49 74.9c10.5 0 16.8-8 16.8-20.4s-6.3-20.4-16.8-20.4c-10.3 0-17 8-17 20.4s6.7 20.4 17 20.4zM294.8 32l12.5 39.2h.5l12-39.2h36L320.5 133h-36.8l11.3-28.8-32.5-72.2h32.3zm-85 70.5c-27 0-47.3-17.8-47.3-44s20.3-44 47.3-44 47.3 17.8 47.3 44-20.3 44-47.3 44zm0-24.5c10.5 0 16.8-8 16.8-19.5s-6.3-19.5-16.8-19.5-16.8 8-16.8 19.5 6.3 19.5 16.8 19.5zm-113.5-46c-9.5 0-15.8 7.5-15.8 18.5v52h-35.5v-70h34v12.5h.5c4.3-8.3 13.3-14.5 26-14.5 18.8 0 30 12 30 33.3v38.7h-35.5V66c0-9.3-4.7-14-12.7-14h9z"/>
                  <path fill="#0668E1" d="M30.5 102.5c-8.5 0-16.5-2.5-22.8-7.3C2.5 91 0 85.5 0 78c0-11 7-22 22.5-32C14 34.3 9 22.5 9 13 9 4 15.8 0 25.3 0c7.5 0 14.5 3.3 21 9.5 6.5-6.2 13.5-9.5 21-9.5 9.5 0 16.3 4 16.3 13 0 9.5-5 21.3-13.5 33 15.5 10 22.5 21 22.5 32 0 7.5-2.5 13-7.8 17.3-6.3 4.8-14.3 7.2-22.8 7.2-8.3 0-15.5-2.3-21-6.8-5.5 4.5-12.7 6.8-21 6.8h.5z"/>
                </svg>
                
                {/* Apple */}
                <svg className="h-8 w-auto opacity-70 hover:opacity-100 transition-opacity" viewBox="0 0 170 170">
                  <path fill="#555555" d="M150.4 130.3c-2.4 5.6-5.2 10.7-8.4 15.4-4.4 6.4-7.9 10.8-10.7 13.3-4.3 4.1-8.8 6.2-13.7 6.3-3.5 0-7.7-1-12.6-3-4.9-2-9.4-3-13.6-3-4.4 0-9.1 1-14.1 3-5 2-9.1 3.1-12.2 3.2-4.7.2-9.3-1.9-13.9-6.4-3-2.7-6.7-7.2-11.2-13.7-4.8-7-8.7-15-11.8-24.1-3.3-9.8-5-19.4-5-28.6 0-10.6 2.3-19.7 6.8-27.4 3.6-6.2 8.3-11 14.3-14.6 6-3.6 12.4-5.4 19.4-5.5 3.7 0 8.6 1.2 14.7 3.4 6 2.3 9.9 3.4 11.6 3.4 1.3 0 5.6-1.3 12.8-3.9 6.9-2.4 12.6-3.4 17.3-3 12.8 1 22.4 6 28.7 15.1-11.4 6.9-17.1 16.6-16.9 29 .1 9.7 3.6 17.7 10.5 24.1 3.1 3 6.6 5.2 10.5 6.9-.8 2.4-1.7 4.7-2.7 6.9l.2-.3zM119.1 7c0 7.6-2.8 14.7-8.3 21.2-6.6 7.8-14.7 12.3-23.4 11.6-.1-.9-.2-1.9-.2-2.9 0-7.3 3.2-15.1 8.8-21.5 2.8-3.2 6.4-5.9 10.7-8 4.3-2.1 8.4-3.2 12.2-3.4.1 1 .2 2 .2 3z"/>
                </svg>
                
                {/* Netflix */}
                <svg className="h-7 w-auto opacity-70 hover:opacity-100 transition-opacity" viewBox="0 0 111 30">
                  <path fill="#E50914" d="M105.1 14.2l5.9 15.6c-2-.3-3.9-.6-5.8-.9l-3.6-9.5-3.7 8.8c-1.9-.3-3.8-.6-5.7-.8l6-14.1-5.6-13.8h5.8l3.2 8.3 3.3-8.3h5.8l-5.6 14.7zm-24.4 7.2V1.7h4.8V24c-1.6-.1-3.2-.2-4.8-.2zm-7 0V1.7h4.8v19.8c-1.6 0-3.2-.1-4.8-.1zm-7.7-5.5c-1.6-.1-3.2-.3-4.8-.5V1.7h4.8V21.4h-4.8v-5.5h4.8zm-12.5 1.7c-1.6-.2-3.2-.4-4.8-.7V1.7h4.8v15.9zm-12.3-2.8c-1.6-.3-3.2-.6-4.8-.9v-14h4.8v14.9zm-12.2-2.8c-1.6-.4-3.2-.8-4.8-1.2V1.7h4.8v11.8zM5.4 1.7h4.8v8.5c-1.6-.5-3.2-1-4.8-1.4V1.7zM.1 14.7l4.9 14.9c.2-.8.4-1.7.6-2.5L.1 14.7zM5.4 1.7v5.9l4.9 14.8V1.7H5.4zm4.9 24.6l-4.9-14v14.8l4.9-.8zm4.9.7l-4.8-14.5v14.3l4.8.2zm4.8-1l-4.8-13.9V27l4.8-.7zm4.8.6l-4.8-13.7v13.5l4.8.2zm4.8-.4l-4.8-13.3v13.2l4.8.1zm4.8-.2l-4.8-13v13l4.8 .1h0zm4.9 0l-4.9-12.6V26h4.9zm4.8 0l-4.8-12.2v12.3l4.8-.1zm4.9.1l-4.9-11.8v11.9l4.9-.1zm4.8.1l-4.8-11.5v11.6l4.8-.1zm4.9.2l-4.9-11.1V26l4.9-.2z"/>
                </svg>
                
                {/* Spotify */}
                <svg className="h-8 w-auto opacity-70 hover:opacity-100 transition-opacity" viewBox="0 0 168 168">
                  <path fill="#1DB954" d="M84 0C37.6 0 0 37.6 0 84s37.6 84 84 84 84-37.6 84-84S130.4 0 84 0zm38.5 121.2c-1.5 2.5-4.7 3.2-7.1 1.7-19.5-11.9-44.1-14.6-73-8-2.8.6-5.6-1.1-6.2-3.9-.6-2.8 1.1-5.6 3.9-6.2 31.7-7.2 58.9-4.1 81 9.3 2.5 1.5 3.2 4.7 1.7 7.1h-.3zm10.3-22.9c-1.9 3.1-5.9 4-9 2.1-22.3-13.7-56.3-17.7-82.7-9.7-3.4 1-7-1-8-4.3-1-3.4 1-7 4.3-8 30.2-9.1 67.8-4.7 93.3 11 3.1 1.9 4 5.9 2.1 9v-.1zm.9-23.8c-26.8-15.9-71-17.4-96.5-9.6-4.1 1.3-8.4-1.1-9.6-5.1-1.3-4.1 1.1-8.4 5.1-9.6 29.3-8.9 78-7.2 108.8 11.1 3.7 2.2 4.9 6.9 2.7 10.6-2.2 3.7-6.9 4.9-10.6 2.7l.1-.1z"/>
                </svg>
                
                {/* Stripe */}
                <svg className="h-8 w-auto opacity-70 hover:opacity-100 transition-opacity" viewBox="0 0 60 25">
                  <path fill="#635BFF" d="M5 11.2C5 7.8 7.8 5 11.2 5h37.6C52.2 5 55 7.8 55 11.2v2.6c0 3.4-2.8 6.2-6.2 6.2H11.2C7.8 20 5 17.2 5 13.8v-2.6z"/>
                  <path fill="#FFFFFF" d="M13.3 9.6c0-.4.4-.7.9-.7h1.6c.5 0 .9.3.9.7v5.7c0 .4-.4.7-.9.7h-1.6c-.5 0-.9-.3-.9-.7V9.6zm7.2 0c0-.4.3-.7.7-.7h1.7c.4 0 .7.3.7.7v3.2l2.3-3.5c.1-.2.4-.4.7-.4h1.9c.5 0 .8.4.6.8l-2.5 3.7 2.7 3.9c.2.4 0 .8-.6.8H27c-.3 0-.5-.1-.7-.4l-2.3-3.5v3.2c0 .4-.3.7-.7.7h-1.7c-.4 0-.7-.3-.7-.7V9.6zm11.9 0c0-.4.3-.7.7-.7h1.7c.4 0 .7.3.7.7v5.7c0 .4-.3.7-.7.7h-1.7c-.4 0-.7-.3-.7-.7V9.6zm7.1 0c0-.4.3-.7.7-.7h1.7c.4 0 .7.3.7.7v3.2l2.3-3.5c.1-.2.4-.4.7-.4h1.9c.5 0 .8.4.6.8l-2.5 3.7 2.7 3.9c.2.4 0 .8-.6.8h-1.9c-.3 0-.5-.1-.7-.4l-2.3-3.5v3.2c0 .4-.3.7-.7.7h-1.7c-.4 0-.7-.3-.7-.7V9.6z"/>
                </svg>
                
                {/* Slack */}
                <svg className="h-8 w-auto opacity-70 hover:opacity-100 transition-opacity" viewBox="0 0 127 127">
                  <path fill="#E01E5A" d="M27.2 80c0 7.3-5.9 13.2-13.2 13.2S.8 87.3.8 80s5.9-13.2 13.2-13.2h13.2V80zm6.6 0c0-7.3 5.9-13.2 13.2-13.2s13.2 5.9 13.2 13.2v33c0 7.3-5.9 13.2-13.2 13.2s-13.2-5.9-13.2-13.2V80z"/>
                  <path fill="#36C5F0" d="M47 27c-7.3 0-13.2-5.9-13.2-13.2S39.7.6 47 .6s13.2 5.9 13.2 13.2V27H47zm0 6.7c7.3 0 13.2 5.9 13.2 13.2s-5.9 13.2-13.2 13.2H13.9C6.6 60.1.7 54.2.7 46.9s5.9-13.2 13.2-13.2H47z"/>
                  <path fill="#2EB67D" d="M99.9 46.9c0-7.3 5.9-13.2 13.2-13.2s13.2 5.9 13.2 13.2-5.9 13.2-13.2 13.2H99.9V46.9zm-6.6 0c0 7.3-5.9 13.2-13.2 13.2s-13.2-5.9-13.2-13.2V13.8C66.9 6.5 72.8.6 80.1.6s13.2 5.9 13.2 13.2v33.1z"/>
                  <path fill="#ECB22E" d="M80.1 99.8c7.3 0 13.2 5.9 13.2 13.2s-5.9 13.2-13.2 13.2-13.2-5.9-13.2-13.2V99.8h13.2zm0-6.6c-7.3 0-13.2-5.9-13.2-13.2s5.9-13.2 13.2-13.2h33.1c7.3 0 13.2 5.9 13.2 13.2s-5.9 13.2-13.2 13.2H80.1z"/>
                </svg>
                
                {/* Airbnb */}
                <svg className="h-8 w-auto opacity-70 hover:opacity-100 transition-opacity" viewBox="0 0 102 32">
                  <path fill="#FF5A5F" d="M29 17.9c-.5-1.4-1.5-2.7-2.8-3.6-1.3-.9-2.8-1.3-4.4-1.3-1.7 0-3.2.5-4.5 1.4-1.3.9-2.3 2.2-2.8 3.8-.4 1.2-.5 2.4-.3 3.7.2 1.2.6 2.4 1.3 3.4.7 1 1.6 1.9 2.7 2.5 1.1.6 2.3.9 3.6.9 1.6 0 3.1-.5 4.4-1.4 1.3-.9 2.2-2.2 2.8-3.7.5-1.6.5-3.3 0-4.8v-.9zm-7.2 7.8c-1.2 0-2.2-.4-3.1-1.2-.9-.8-1.4-1.8-1.4-3 0-.4 0-.8.1-1.2.2-.8.6-1.5 1.2-2 .6-.6 1.3-.9 2.2-1.1.3 0 .6-.1 1-.1 1.2 0 2.2.4 3.1 1.2.8.8 1.3 1.8 1.4 3v.2c0 .4 0 .8-.1 1.1-.2.8-.6 1.5-1.2 2-.6.6-1.4 1-2.3 1.1h-.9z"/>
                </svg>
                
                {/* JPMorgan */}
                <div className="flex items-center h-8 opacity-70 hover:opacity-100 transition-opacity">
                  <span className="text-lg font-bold text-[#003087]">JPMorgan</span>
                </div>
                
                {/* Goldman Sachs */}
                <div className="flex items-center h-8 opacity-70 hover:opacity-100 transition-opacity">
                  <span className="text-lg font-bold text-[#7399C6]">Goldman Sachs</span>
                </div>
                
                {/* TD Bank */}
                <div className="flex items-center h-8 opacity-70 hover:opacity-100 transition-opacity">
                  <span className="text-lg font-bold text-[#34A853]">TD Bank</span>
                </div>
                
                {/* RBC */}
                <div className="flex items-center h-8 opacity-70 hover:opacity-100 transition-opacity">
                  <span className="text-lg font-bold text-[#0051A5]">RBC</span>
                </div>
                
                {/* Deloitte */}
                <div className="flex items-center h-8 opacity-70 hover:opacity-100 transition-opacity">
                  <span className="text-lg font-bold text-[#86BC25]">Deloitte</span>
                </div>
                
                {/* KPMG */}
                <div className="flex items-center h-8 opacity-70 hover:opacity-100 transition-opacity">
                  <span className="text-lg font-bold text-[#00338D]">KPMG</span>
                </div>
              </div>
              
              {/* Duplicate set for seamless loop */}
              <div className="flex items-center gap-16 px-8 shrink-0">
                {/* Google */}
                <svg className="h-8 w-auto opacity-70 hover:opacity-100 transition-opacity" viewBox="0 0 272 92">
                  <path fill="#EA4335" d="M115.75 47.18c0 12.77-9.99 22.18-22.25 22.18s-22.25-9.41-22.25-22.18C71.25 34.32 81.24 25 93.5 25s22.25 9.32 22.25 22.18zm-9.74 0c0-7.98-5.79-13.44-12.51-13.44S80.99 39.2 80.99 47.18c0 7.9 5.79 13.44 12.51 13.44s12.51-5.55 12.51-13.44z"/>
                  <path fill="#FBBC05" d="M163.75 47.18c0 12.77-9.99 22.18-22.25 22.18s-22.25-9.41-22.25-22.18c0-12.85 9.99-22.18 22.25-22.18s22.25 9.32 22.25 22.18zm-9.74 0c0-7.98-5.79-13.44-12.51-13.44s-12.51 5.46-12.51 13.44c0 7.9 5.79 13.44 12.51 13.44s12.51-5.55 12.51-13.44z"/>
                  <path fill="#4285F4" d="M209.75 26.34v39.82c0 16.38-9.66 23.07-21.08 23.07-10.75 0-17.22-7.19-19.66-13.07l8.48-3.53c1.51 3.61 5.21 7.87 11.17 7.87 7.31 0 11.84-4.51 11.84-13v-3.19h-.34c-2.18 2.69-6.38 5.04-11.68 5.04-11.09 0-21.25-9.66-21.25-22.09 0-12.52 10.16-22.26 21.25-22.26 5.29 0 9.49 2.35 11.68 4.96h.34v-3.61h9.25zm-8.56 20.92c0-7.81-5.21-13.52-11.84-13.52-6.72 0-12.35 5.71-12.35 13.52 0 7.73 5.63 13.36 12.35 13.36 6.63 0 11.84-5.63 11.84-13.36z"/>
                  <path fill="#34A853" d="M225 3v65h-9.5V3h9.5z"/>
                  <path fill="#EA4335" d="M262.02 54.48l7.56 5.04c-2.44 3.61-8.32 9.83-18.48 9.83-12.6 0-22.01-9.74-22.01-22.18 0-13.19 9.49-22.18 20.92-22.18 11.51 0 17.14 9.16 18.98 14.11l1.01 2.52-29.65 12.28c2.27 4.45 5.8 6.72 10.75 6.72 4.96 0 8.4-2.44 10.92-6.14zm-23.27-7.98l19.82-8.23c-1.09-2.77-4.37-4.7-8.23-4.7-4.95 0-11.84 4.37-11.59 12.93z"/>
                  <path fill="#4285F4" d="M35.29 41.41V32H67c.31 1.64.47 3.58.47 5.68 0 7.06-1.93 15.79-8.15 22.01-6.05 6.3-13.78 9.66-24.02 9.66C16.32 69.35.36 53.89.36 34.91.36 15.93 16.32.47 35.3.47c10.5 0 17.98 4.12 23.6 9.49l-6.64 6.64c-4.03-3.78-9.49-6.72-16.97-6.72-13.86 0-24.7 11.17-24.7 25.03 0 13.86 10.84 25.03 24.7 25.03 8.99 0 14.11-3.61 17.39-6.89 2.66-2.66 4.41-6.46 5.1-11.65l-22.49.01z"/>
                </svg>
                
                {/* Microsoft */}
                <svg className="h-7 w-auto opacity-70 hover:opacity-100 transition-opacity" viewBox="0 0 318 69">
                  <path fill="#737373" d="M99.1 18.9v30.4h-4.7V23.1h-.1l-11.5 26.2h-3.1L68.1 23.1H68v26.2h-4.4V18.9h6.5l10.7 25h.2l11.4-25h6.7zm5.4 5.9h4.3v3.2h.1c1.5-2.5 4-3.7 7.1-3.7 5.6 0 8.3 3.4 8.3 9.1v16h-4.5V34.2c0-4.2-1.7-6.2-5.2-6.2-4 0-5.8 2.4-5.8 7.4v14h-4.3V24.8zm33.6 20.6h-.1v14h-4.5V24.8h4.3v3.5h.1c1.6-2.7 4.4-4 7.6-4 6.2 0 9.6 4.9 9.6 12.1 0 7.2-3.7 12.1-9.9 12.1-3.1 0-5.6-1.3-7.1-3.1zm-.1-8.7c0 5.1 2.4 8.3 6.5 8.3 4.2 0 6.5-3.4 6.5-8.6 0-5.1-2.2-8.4-6.4-8.4-4.3 0-6.6 3.4-6.6 8.7zm24.3-11.9h4.5v3.7h.1c1.3-2.8 3.8-4.2 7-4.2.9 0 1.5.1 2.2.2v4.3c-.8-.2-1.5-.3-2.4-.3-4.6 0-7 2.9-7 7.8v13h-4.5V24.8h.1zm17.8 12.1c0 5 2.5 8.2 6.8 8.2 3.2 0 5.2-1.7 5.9-4.7h4.6c-1 5.3-4.8 8.4-10.6 8.4-7.2 0-11.3-4.9-11.3-12.1 0-6.9 4.2-12.1 11.2-12.1 7.2 0 11.1 5.4 10.7 12.4h-17.3v-.1zm12.7-3.2c-.3-4.2-2.6-6.7-6.2-6.7-3.7 0-6.1 2.7-6.5 6.7h12.7zm8.4-5.9c0-6.1 4.3-9.7 11.4-10l9.3-.5v-2.6c0-4.4-2.4-6.4-6.6-6.4-3.7 0-6.1 1.6-6.5 4.7h-4.7c.4-5.3 4.8-8.6 11.4-8.6 7 0 11 3.5 11 9.7v21.3h-4.3v-4h-.1c-1.7 3-5 4.5-8.9 4.5-5.4.1-9-3.3-9-8.1zm20.6-2.6v-3l-8.7.5c-4.4.3-6.6 1.9-6.6 5 0 3 2.3 4.9 5.9 4.9 4.8.1 9.4-2.8 9.4-7.4zm11.1-10.4h4.5v3.7h.1c1.3-2.8 3.8-4.2 7-4.2.9 0 1.5.1 2.2.2v4.3c-.8-.2-1.5-.3-2.4-.3-4.6 0-7 2.9-7 7.8v13h-4.5V24.8h.1zm35.3 7.4h-4.6c-.4-3-2.6-4.7-6.3-4.7-3.4 0-5.8 1.4-5.8 3.8 0 2.1 1.5 3.2 4.9 4l4 .8c5.8 1.2 8.3 3.6 8.3 7.7 0 5.2-4.7 8.5-11.1 8.5-6.8 0-11.4-3.2-11.8-8.8h4.7c.5 3.3 3 5 7.2 5 3.9 0 6.4-1.6 6.4-4.1 0-2.2-1.4-3.4-5-4.2l-4.3-1c-5.4-1.2-7.8-3.8-7.8-7.9 0-5 4.4-8.3 10.6-8.3 6.3.1 10.3 3.4 10.6 9.2zm5.3 4.7c0-7 4.2-12.1 10.8-12.1 6.7 0 10.8 5.1 10.8 12.1 0 7.1-4.1 12.1-10.8 12.1-6.7.1-10.8-5-10.8-12.1zm17 0c0-5.1-2.4-8.4-6.3-8.4-3.9 0-6.2 3.3-6.2 8.4s2.4 8.4 6.3 8.4 6.2-3.4 6.2-8.4zm14.2-12.1v-6.1h4.5v6.1h5.4v3.7h-5.4v13.9c0 2.4.9 3.4 3.3 3.4h2.1v3.6c-1.2.2-2.3.3-3.6.3-4.9 0-6.3-2-6.3-6.5V28.5h-4v-3.7h4z"/>
                  <path fill="#F25022" d="M0 0h32.7v32.7H0z"/>
                  <path fill="#7FBA00" d="M36.4 0h32.7v32.7H36.4z"/>
                  <path fill="#00A4EF" d="M0 36.4h32.7v32.7H0z"/>
                  <path fill="#FFB900" d="M36.4 36.4h32.7v32.7H36.4z"/>
                </svg>
                
                {/* Amazon */}
                <svg className="h-7 w-auto opacity-70 hover:opacity-100 transition-opacity" viewBox="0 0 603 182">
                  <path fill="#FF9900" d="M374.1 142.1c-34.5 25.5-84.6 39-127.7 39-60.5 0-114.9-22.4-156.1-59.6-3.2-2.9-.3-6.9 3.6-4.6 44.5 25.9 99.4 41.4 156.2 41.4 38.3 0 80.4-7.9 119.2-24.4 5.8-2.5 10.7 3.8 4.8 8.2z"/>
                  <path fill="#FF9900" d="M387.9 126.5c-4.4-5.6-29.1-2.7-40.2-1.3-3.4.4-3.9-2.5-.9-4.7 19.7-13.8 52-9.8 55.8-5.2 3.8 4.7-1 37.1-19.5 52.6-2.8 2.4-5.5 1.1-4.3-2 4.2-10.4 13.5-33.8 9.1-39.4z"/>
                  <path fill="#232F3E" d="M348.5 21.2V6.4c0-2.2 1.7-3.7 3.7-3.7h65.6c2.1 0 3.8 1.5 3.8 3.7v12.7c0 2.1-1.8 4.9-5 9.3l-34 48.6c12.6-.3 26 1.6 37.4 8 2.6 1.5 3.3 3.6 3.5 5.8v15.8c0 2.2-2.4 4.7-4.9 3.4-20.5-10.8-47.8-12-70.5.1-2.3 1.2-4.7-1.3-4.7-3.5V91.3c0-2.4 0-6.6 2.5-10.3l39.4-56.5h-34.3c-2.1 0-3.8-1.5-3.8-3.7l.3.4z"/>
                </svg>
                
                {/* Meta */}
                <svg className="h-7 w-auto opacity-70 hover:opacity-100 transition-opacity" viewBox="0 0 512 105">
                  <path fill="#0668E1" d="M471.5 23.4c6.5 0 11.8-5.3 11.8-11.7C483.3 5.3 478 0 471.5 0s-11.8 5.3-11.8 11.7c0 6.5 5.3 11.7 11.8 11.7zm-17.7 79V32h35.5v70.3h-35.5z"/>
                </svg>
                
                {/* Apple */}
                <svg className="h-8 w-auto opacity-70 hover:opacity-100 transition-opacity" viewBox="0 0 170 170">
                  <path fill="#555555" d="M150.4 130.3c-2.4 5.6-5.2 10.7-8.4 15.4-4.4 6.4-7.9 10.8-10.7 13.3-4.3 4.1-8.8 6.2-13.7 6.3-3.5 0-7.7-1-12.6-3-4.9-2-9.4-3-13.6-3-4.4 0-9.1 1-14.1 3-5 2-9.1 3.1-12.2 3.2-4.7.2-9.3-1.9-13.9-6.4-3-2.7-6.7-7.2-11.2-13.7-4.8-7-8.7-15-11.8-24.1-3.3-9.8-5-19.4-5-28.6 0-10.6 2.3-19.7 6.8-27.4 3.6-6.2 8.3-11 14.3-14.6 6-3.6 12.4-5.4 19.4-5.5 3.7 0 8.6 1.2 14.7 3.4 6 2.3 9.9 3.4 11.6 3.4 1.3 0 5.6-1.3 12.8-3.9 6.9-2.4 12.6-3.4 17.3-3 12.8 1 22.4 6 28.7 15.1-11.4 6.9-17.1 16.6-16.9 29 .1 9.7 3.6 17.7 10.5 24.1 3.1 3 6.6 5.2 10.5 6.9-.8 2.4-1.7 4.7-2.7 6.9l.2-.3z"/>
                </svg>
                
                {/* Netflix */}
                <svg className="h-7 w-auto opacity-70 hover:opacity-100 transition-opacity" viewBox="0 0 111 30">
                  <path fill="#E50914" d="M105.1 14.2l5.9 15.6c-2-.3-3.9-.6-5.8-.9l-3.6-9.5-3.7 8.8c-1.9-.3-3.8-.6-5.7-.8l6-14.1-5.6-13.8h5.8l3.2 8.3 3.3-8.3h5.8l-5.6 14.7z"/>
                </svg>
                
                {/* Spotify */}
                <svg className="h-8 w-auto opacity-70 hover:opacity-100 transition-opacity" viewBox="0 0 168 168">
                  <path fill="#1DB954" d="M84 0C37.6 0 0 37.6 0 84s37.6 84 84 84 84-37.6 84-84S130.4 0 84 0zm38.5 121.2c-1.5 2.5-4.7 3.2-7.1 1.7-19.5-11.9-44.1-14.6-73-8-2.8.6-5.6-1.1-6.2-3.9-.6-2.8 1.1-5.6 3.9-6.2 31.7-7.2 58.9-4.1 81 9.3 2.5 1.5 3.2 4.7 1.7 7.1h-.3z"/>
                </svg>
                
                {/* Stripe */}
                <svg className="h-8 w-auto opacity-70 hover:opacity-100 transition-opacity" viewBox="0 0 60 25">
                  <path fill="#635BFF" d="M5 11.2C5 7.8 7.8 5 11.2 5h37.6C52.2 5 55 7.8 55 11.2v2.6c0 3.4-2.8 6.2-6.2 6.2H11.2C7.8 20 5 17.2 5 13.8v-2.6z"/>
                </svg>
                
                {/* Slack */}
                <svg className="h-8 w-auto opacity-70 hover:opacity-100 transition-opacity" viewBox="0 0 127 127">
                  <path fill="#E01E5A" d="M27.2 80c0 7.3-5.9 13.2-13.2 13.2S.8 87.3.8 80s5.9-13.2 13.2-13.2h13.2V80zm6.6 0c0-7.3 5.9-13.2 13.2-13.2s13.2 5.9 13.2 13.2v33c0 7.3-5.9 13.2-13.2 13.2s-13.2-5.9-13.2-13.2V80z"/>
                  <path fill="#36C5F0" d="M47 27c-7.3 0-13.2-5.9-13.2-13.2S39.7.6 47 .6s13.2 5.9 13.2 13.2V27H47zm0 6.7c7.3 0 13.2 5.9 13.2 13.2s-5.9 13.2-13.2 13.2H13.9C6.6 60.1.7 54.2.7 46.9s5.9-13.2 13.2-13.2H47z"/>
                  <path fill="#2EB67D" d="M99.9 46.9c0-7.3 5.9-13.2 13.2-13.2s13.2 5.9 13.2 13.2-5.9 13.2-13.2 13.2H99.9V46.9zm-6.6 0c0 7.3-5.9 13.2-13.2 13.2s-13.2-5.9-13.2-13.2V13.8C66.9 6.5 72.8.6 80.1.6s13.2 5.9 13.2 13.2v33.1z"/>
                  <path fill="#ECB22E" d="M80.1 99.8c7.3 0 13.2 5.9 13.2 13.2s-5.9 13.2-13.2 13.2-13.2-5.9-13.2-13.2V99.8h13.2zm0-6.6c-7.3 0-13.2-5.9-13.2-13.2s5.9-13.2 13.2-13.2h33.1c7.3 0 13.2 5.9 13.2 13.2s-5.9 13.2-13.2 13.2H80.1z"/>
                </svg>
                
                {/* Airbnb */}
                <svg className="h-8 w-auto opacity-70 hover:opacity-100 transition-opacity" viewBox="0 0 102 32">
                  <path fill="#FF5A5F" d="M29 17.9c-.5-1.4-1.5-2.7-2.8-3.6-1.3-.9-2.8-1.3-4.4-1.3-1.7 0-3.2.5-4.5 1.4-1.3.9-2.3 2.2-2.8 3.8-.4 1.2-.5 2.4-.3 3.7.2 1.2.6 2.4 1.3 3.4.7 1 1.6 1.9 2.7 2.5 1.1.6 2.3.9 3.6.9 1.6 0 3.1-.5 4.4-1.4 1.3-.9 2.2-2.2 2.8-3.7.5-1.6.5-3.3 0-4.8v-.9z"/>
                </svg>
                
                {/* Banks - text */}
                <div className="flex items-center h-8 opacity-70 hover:opacity-100 transition-opacity">
                  <span className="text-lg font-bold text-[#003087]">JPMorgan</span>
                </div>
                <div className="flex items-center h-8 opacity-70 hover:opacity-100 transition-opacity">
                  <span className="text-lg font-bold text-[#7399C6]">Goldman Sachs</span>
                </div>
                <div className="flex items-center h-8 opacity-70 hover:opacity-100 transition-opacity">
                  <span className="text-lg font-bold text-[#34A853]">TD Bank</span>
                </div>
                <div className="flex items-center h-8 opacity-70 hover:opacity-100 transition-opacity">
                  <span className="text-lg font-bold text-[#0051A5]">RBC</span>
                </div>
                <div className="flex items-center h-8 opacity-70 hover:opacity-100 transition-opacity">
                  <span className="text-lg font-bold text-[#86BC25]">Deloitte</span>
                </div>
                <div className="flex items-center h-8 opacity-70 hover:opacity-100 transition-opacity">
                  <span className="text-lg font-bold text-[#00338D]">KPMG</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Why Choose Us Section */}
        <section id="how-it-works" className="max-w-6xl mx-auto py-20">
          <div className="text-center mb-16 animate-fade-in">
            <div className="inline-flex items-center gap-2 bg-indigo-500/10 text-indigo-400 px-4 py-2 rounded-full text-sm font-medium mb-6">
              <Chrome className="w-4 h-4" />
              Chrome Extension
            </div>
            <h2 className="text-3xl lg:text-4xl font-bold text-foreground mb-4">
              Apply to jobs in seconds, not hours
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Our Chrome extension lives right where you job hunt.{" "}
              <span className="text-foreground font-semibold">Find a job. Click. Apply. Done.</span>
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

          {/* How It Works Steps */}
          <div className="mt-20">
            <h3 className="text-2xl font-bold text-foreground text-center mb-12">
              How it works
            </h3>
            <div className="grid md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto mb-4 text-xl font-bold">
                  1
                </div>
                <h4 className="font-semibold text-foreground mb-2">Install Extension</h4>
                <p className="text-sm text-muted-foreground">Add our Chrome extension in one click. Takes 10 seconds.</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto mb-4 text-xl font-bold">
                  2
                </div>
                <h4 className="font-semibold text-foreground mb-2">Build Your Profile</h4>
                <p className="text-sm text-muted-foreground">Enter your info once. We'll use it to fill every application.</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-amber-500/20 text-amber-400 flex items-center justify-center mx-auto mb-4 text-xl font-bold">
                  3
                </div>
                <h4 className="font-semibold text-foreground mb-2">Find a Job</h4>
                <p className="text-sm text-muted-foreground">Browse Greenhouse, Lever, Ashby — wherever jobs live.</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center mx-auto mb-4 text-xl font-bold">
                  4
                </div>
                <h4 className="font-semibold text-foreground mb-2">Click & Apply</h4>
                <p className="text-sm text-muted-foreground">One click fills everything. Review, submit, and track automatically.</p>
              </div>
            </div>
          </div>

          {/* CTA Button */}
          <div className="text-center mt-12">
            <Button
              size="lg"
              className="bg-indigo-500 hover:bg-indigo-600 text-white px-8 py-6 text-lg rounded-full shadow-lg shadow-indigo-500/25"
              onClick={() => window.open('/api/downloads/browser-extension.zip', '_blank')}
            >
              <Download className="w-5 h-5 mr-2" />
              Download Chrome Extension
            </Button>
            <p className="text-sm text-muted-foreground mt-3">Free forever. No credit card required.</p>
          </div>
        </section>

        {/* Testimonials Section */}
        <section className="max-w-6xl mx-auto py-20">
          <div className="text-center mb-12">
            <h2 className="text-3xl lg:text-4xl font-bold text-foreground mb-4">
              What our users are saying
            </h2>
            <p className="text-lg text-muted-foreground">
              Real results from job seekers using the extension
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
                  "The extension is a game-changer. I used to spend 20 minutes per application — now it's literally 30 seconds. Applied to 15 jobs in one evening!"
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
                  "Finally, an auto-fill that actually works with Greenhouse dropdowns. The tailored resume for each job is the cherry on top."
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
                  "I love that it tracks my applications automatically. No more spreadsheets! Plus the 'What to do next' feature reminds me to follow up."
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
                onClick={() => navigate('/auth')}
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
            <span className="text-sm text-muted-foreground">© 2025 CareerCopilot AI. All rights reserved.</span>
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
