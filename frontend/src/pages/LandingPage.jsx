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
      title: "One-Click Auto-Fill",
      description: "Name, experience, work authorization — filled instantly on any job site.",
      highlight: "No more copy-pasting. No more typos.",
      color: "text-indigo-500",
      bgColor: "bg-indigo-50",
    },
    {
      icon: FileText,
      title: "AI-Tailored Documents",
      description: "Every application gets a customized resume and cover letter. Automatically.",
      highlight: "Every application is customized. Automatically.",
      color: "text-emerald-500",
      bgColor: "bg-emerald-50",
    },
    {
      icon: MousePointerClick,
      title: "Smart Form Handling",
      description: "Dropdowns, dates, checkboxes — we fill the annoying fields correctly.",
      highlight: "Even the annoying fields get filled correctly.",
      color: "text-amber-500",
      bgColor: "bg-amber-50",
    },
    {
      icon: Target,
      title: "Track Every Application Automatically",
      description: "Hit submit, and we log it to your dashboard instantly. Follow-up reminders, interview prep, next steps — all in one place.",
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
          <div className="flex items-center gap-1">
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
                {[
                  { name: "Google", logo: "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png" },
                  { name: "Microsoft", logo: "https://img-prod-cms-rt-microsoft-com.akamaized.net/cms/api/am/imageFileData/RE1Mu3b?ver=5c31" },
                  { name: "Amazon", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Amazon_logo.svg/200px-Amazon_logo.svg.png" },
                  { name: "Apple", logo: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 384 512'%3E%3Cpath d='M318.7 268.7c-.2-36.7 16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 20.7-88.5 20.7-15 0-49.4-19.7-76.4-19.7C63.3 141.2 4 184.8 4 273.5q0 39.3 14.4 81.2c12.8 36.7 59 126.7 107.2 125.2 25.2-.6 43-17.9 75.8-17.9 31.8 0 48.3 17.9 76.4 17.9 48.6-.7 90.4-82.5 102.6-119.3-65.2-30.7-61.7-90-61.7-91.9zm-56.6-164.2c27.3-32.4 24.8-62.1 24-72.5-24.1 1.4-52 16.4-67.9 34.9-17.5 19.8-27.8 44.3-25.6 71.9 26.1 2 49.9-11.4 69.5-34.3z'/%3E%3C/svg%3E" },
                  { name: "Netflix", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Netflix_2015_logo.svg/200px-Netflix_2015_logo.svg.png" },
                  { name: "Uber", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Uber_logo_2018.svg/200px-Uber_logo_2018.svg.png" },
                  { name: "Airbnb", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Airbnb_Logo_B%C3%A9lo.svg/200px-Airbnb_Logo_B%C3%A9lo.svg.png" },
                  { name: "Spotify", logo: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 496 512'%3E%3Cpath fill='%231DB954' d='M248 8C111.1 8 0 119.1 0 256s111.1 248 248 248 248-111.1 248-248S384.9 8 248 8zm100.7 364.9c-4.2 0-6.8-1.3-10.7-3.6-62.4-37.6-135-39.2-206.7-24.5-3.9 1-9 2.6-11.9 2.6-9.7 0-15.8-7.7-15.8-15.8 0-10.3 6.1-15.2 13.6-16.8 81.9-18.1 165.6-16.5 237 26.2 6.1 3.9 9.7 7.4 9.7 16.5s-7.1 15.4-15.2 15.4zm26.9-65.6c-5.2 0-8.7-2.3-12.3-4.2-62.5-37-155.7-51.9-238.6-29.4-4.8 1.3-7.4 2.6-11.9 2.6-10.7 0-19.4-8.7-19.4-19.4s5.2-17.8 15.5-20.7c27.8-7.8 56.2-13.6 97.8-13.6 64.9 0 127.6 16.1 177 45.5 8.1 4.8 11.3 11 11.3 19.7-.1 10.8-8.5 19.5-19.4 19.5zm31-76.2c-5.2 0-8.4-1.3-12.9-3.9-71.2-42.5-198.5-52.7-280.9-29.7-3.6 1-8.1 2.6-12.9 2.6-13.2 0-23.3-10.3-23.3-23.6 0-13.6 8.4-21.3 17.4-23.9 35.2-10.3 74.6-15.2 117.5-15.2 73 0 149.5 15.2 205.4 47.8 7.8 4.5 12.9 10.7 12.9 22.6 0 13.6-11 23.3-23.2 23.3z'/%3E%3C/svg%3E" },
                  { name: "Shopify", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Shopify_logo_2018.svg/200px-Shopify_logo_2018.svg.png" },
                  { name: "Stripe", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Stripe_Logo%2C_revised_2016.svg/200px-Stripe_Logo%2C_revised_2016.svg.png" },
                  { name: "Slack", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/Slack_icon_2019.svg/100px-Slack_icon_2019.svg.png" },
                  { name: "LinkedIn", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/LinkedIn_logo_initials.png/100px-LinkedIn_logo_initials.png" },
                  { name: "Salesforce", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Salesforce.com_logo.svg/200px-Salesforce.com_logo.svg.png" },
                  { name: "Adobe", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Adobe_Corporate_Logo.svg/150px-Adobe_Corporate_Logo.svg.png" },
                  { name: "JPMorgan", logo: null, color: "#003087" },
                  { name: "Goldman Sachs", logo: null, color: "#7399C6" },
                  { name: "Deloitte", logo: null, color: "#86BC25" },
                  { name: "TD Bank", logo: null, color: "#34A853" },
                  { name: "RBC", logo: null, color: "#0051A5" },
                ].map((company, i) => (
                  <div 
                    key={`logo-1-${i}`}
                    className="flex items-center justify-center h-10 opacity-70 hover:opacity-100 transition-opacity"
                  >
                    {company.logo ? (
                      <img 
                        src={company.logo}
                        alt={company.name}
                        className="h-8 w-auto object-contain"
                        loading="lazy"
                      />
                    ) : (
                      <span 
                        className="text-lg font-bold whitespace-nowrap"
                        style={{ color: company.color }}
                      >
                        {company.name}
                      </span>
                    )}
                  </div>
                ))}
              </div>
              {/* Duplicate set for seamless loop */}
              <div className="flex items-center gap-16 px-8 shrink-0">
                {[
                  { name: "Google", logo: "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png" },
                  { name: "Microsoft", logo: "https://img-prod-cms-rt-microsoft-com.akamaized.net/cms/api/am/imageFileData/RE1Mu3b?ver=5c31" },
                  { name: "Amazon", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Amazon_logo.svg/200px-Amazon_logo.svg.png" },
                  { name: "Apple", logo: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 384 512'%3E%3Cpath d='M318.7 268.7c-.2-36.7 16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 20.7-88.5 20.7-15 0-49.4-19.7-76.4-19.7C63.3 141.2 4 184.8 4 273.5q0 39.3 14.4 81.2c12.8 36.7 59 126.7 107.2 125.2 25.2-.6 43-17.9 75.8-17.9 31.8 0 48.3 17.9 76.4 17.9 48.6-.7 90.4-82.5 102.6-119.3-65.2-30.7-61.7-90-61.7-91.9zm-56.6-164.2c27.3-32.4 24.8-62.1 24-72.5-24.1 1.4-52 16.4-67.9 34.9-17.5 19.8-27.8 44.3-25.6 71.9 26.1 2 49.9-11.4 69.5-34.3z'/%3E%3C/svg%3E" },
                  { name: "Netflix", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Netflix_2015_logo.svg/200px-Netflix_2015_logo.svg.png" },
                  { name: "Uber", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Uber_logo_2018.svg/200px-Uber_logo_2018.svg.png" },
                  { name: "Airbnb", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Airbnb_Logo_B%C3%A9lo.svg/200px-Airbnb_Logo_B%C3%A9lo.svg.png" },
                  { name: "Spotify", logo: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 496 512'%3E%3Cpath fill='%231DB954' d='M248 8C111.1 8 0 119.1 0 256s111.1 248 248 248 248-111.1 248-248S384.9 8 248 8zm100.7 364.9c-4.2 0-6.8-1.3-10.7-3.6-62.4-37.6-135-39.2-206.7-24.5-3.9 1-9 2.6-11.9 2.6-9.7 0-15.8-7.7-15.8-15.8 0-10.3 6.1-15.2 13.6-16.8 81.9-18.1 165.6-16.5 237 26.2 6.1 3.9 9.7 7.4 9.7 16.5s-7.1 15.4-15.2 15.4zm26.9-65.6c-5.2 0-8.7-2.3-12.3-4.2-62.5-37-155.7-51.9-238.6-29.4-4.8 1.3-7.4 2.6-11.9 2.6-10.7 0-19.4-8.7-19.4-19.4s5.2-17.8 15.5-20.7c27.8-7.8 56.2-13.6 97.8-13.6 64.9 0 127.6 16.1 177 45.5 8.1 4.8 11.3 11 11.3 19.7-.1 10.8-8.5 19.5-19.4 19.5zm31-76.2c-5.2 0-8.4-1.3-12.9-3.9-71.2-42.5-198.5-52.7-280.9-29.7-3.6 1-8.1 2.6-12.9 2.6-13.2 0-23.3-10.3-23.3-23.6 0-13.6 8.4-21.3 17.4-23.9 35.2-10.3 74.6-15.2 117.5-15.2 73 0 149.5 15.2 205.4 47.8 7.8 4.5 12.9 10.7 12.9 22.6 0 13.6-11 23.3-23.2 23.3z'/%3E%3C/svg%3E" },
                  { name: "Shopify", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Shopify_logo_2018.svg/200px-Shopify_logo_2018.svg.png" },
                  { name: "Stripe", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Stripe_Logo%2C_revised_2016.svg/200px-Stripe_Logo%2C_revised_2016.svg.png" },
                  { name: "Slack", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/Slack_icon_2019.svg/100px-Slack_icon_2019.svg.png" },
                  { name: "LinkedIn", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/LinkedIn_logo_initials.png/100px-LinkedIn_logo_initials.png" },
                  { name: "Salesforce", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Salesforce.com_logo.svg/200px-Salesforce.com_logo.svg.png" },
                  { name: "Adobe", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Adobe_Corporate_Logo.svg/150px-Adobe_Corporate_Logo.svg.png" },
                  { name: "JPMorgan", logo: null, color: "#003087" },
                  { name: "Goldman Sachs", logo: null, color: "#7399C6" },
                  { name: "Deloitte", logo: null, color: "#86BC25" },
                  { name: "TD Bank", logo: null, color: "#34A853" },
                  { name: "RBC", logo: null, color: "#0051A5" },
                ].map((company, i) => (
                  <div 
                    key={`logo-2-${i}`}
                    className="flex items-center justify-center h-10 opacity-70 hover:opacity-100 transition-opacity"
                  >
                    {company.logo ? (
                      <img 
                        src={company.logo}
                        alt={company.name}
                        className="h-8 w-auto object-contain"
                        loading="lazy"
                      />
                    ) : (
                      <span 
                        className="text-lg font-bold whitespace-nowrap"
                        style={{ color: company.color }}
                      >
                        {company.name}
                      </span>
                    )}
                  </div>
                ))}
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
                <p className="text-sm text-muted-foreground">Browse any job board or company careers page.</p>
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
                  "Finally, an auto-fill that actually works with every job site's dropdowns. The tailored resume for each job is the cherry on top."
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
            <span className="text-sm text-muted-foreground">© 2025 MyCareerCoPilot. All rights reserved.</span>
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
