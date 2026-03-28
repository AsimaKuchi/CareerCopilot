import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  ArrowRight,
  CheckCircle,
  Shield,
  Clock,
  Users,
  XCircle,
  AlertTriangle,
  MapPin,
  Zap,
  Chrome,
  MousePointerClick,
  Download,
  LayoutDashboard,
  Target,
  FileText,
  Sparkles,
} from "lucide-react";
import { API } from "@/App";

const handleGoogleLogin = () => {
  const redirectUrl = window.location.origin + "/dashboard";
  window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
};

export default function LandingPage() {
  const navigate = useNavigate();
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    fetch(`${API}/auth/me`, { credentials: "include" })
      .then((res) => { if (res.ok) setIsLoggedIn(true); })
      .catch(() => {});
  }, []);

  const features = [
    {
      icon: Chrome,
      title: "One-Click Auto-Fill",
      description: "Name, experience, work authorization — filled instantly on any job site.",
      highlight: "No more copy-pasting. No more typos.",
    },
    {
      icon: FileText,
      title: "AI-Tailored Documents",
      description: "Every application gets a customized resume and cover letter. Automatically.",
      highlight: "Every application is customized. Automatically.",
    },
    {
      icon: MousePointerClick,
      title: "Smart Form Handling",
      description: "Dropdowns, dates, checkboxes — we fill the annoying fields correctly.",
      highlight: "Even the annoying fields get filled correctly.",
    },
    {
      icon: Target,
      title: "Track Every Application",
      description: "Hit submit, and we log it to your dashboard instantly. Follow-up reminders, interview prep, next steps — all in one place.",
      highlight: "Apply on their site. Track on yours.",
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

  const metrics = [
    { icon: Clock, value: "25+ min", label: "Average time saved per application" },
    { icon: Zap, value: "3-5x faster", label: "From job page to ready to submit" },
    { icon: Target, value: "Quality-first", label: "Strong-fit roles only" },
    { icon: Shield, value: "100% human", label: "You approve every submission" },
  ];

  const steps = [
    { num: "1", title: "Install Extension", desc: "Add our Chrome extension in one click. Takes 10 seconds.", color: "bg-indigo-50 text-indigo-600" },
    { num: "2", title: "Build Your Profile", desc: "Enter your info once. We'll use it to fill every application.", color: "bg-emerald-50 text-emerald-600" },
    { num: "3", title: "Find a Job", desc: "Browse any job board or company careers page.", color: "bg-amber-50 text-amber-600" },
    { num: "4", title: "Click & Apply", desc: "One click fills everything. Review, submit, and track automatically.", color: "bg-blue-50 text-blue-600" },
  ];

  const reviews = [
    { text: "The extension is a game-changer. I used to spend 20 minutes per application — now it's literally 30 seconds. Applied to 15 jobs in one evening!", name: "Sarah Chen", role: "Software Developer", loc: "Toronto, ON" },
    { text: "Finally, an auto-fill that actually works with every job site's dropdowns. The tailored resume for each job is the cherry on top.", name: "Marcus Miller", role: "Marketing Manager", loc: "Ottawa, ON" },
    { text: "I love that it tracks my applications automatically. No more spreadsheets! Plus the 'What to do next' feature reminds me to follow up.", name: "Priya Sharma", role: "Data Analyst", loc: "Mississauga, ON" },
  ];

  const logos = [
    { name: "Google", logo: "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png" },
    { name: "Microsoft", logo: "https://img-prod-cms-rt-microsoft-com.akamaized.net/cms/api/am/imageFileData/RE1Mu3b?ver=5c31" },
    { name: "Amazon", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Amazon_logo.svg/200px-Amazon_logo.svg.png" },
    { name: "Apple", logo: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 384 512'%3E%3Cpath d='M318.7 268.7c-.2-36.7 16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 20.7-88.5 20.7-15 0-49.4-19.7-76.4-19.7C63.3 141.2 4 184.8 4 273.5q0 39.3 14.4 81.2c12.8 36.7 59 126.7 107.2 125.2 25.2-.6 43-17.9 75.8-17.9 31.8 0 48.3 17.9 76.4 17.9 48.6-.7 90.4-82.5 102.6-119.3-65.2-30.7-61.7-90-61.7-91.9zm-56.6-164.2c27.3-32.4 24.8-62.1 24-72.5-24.1 1.4-52 16.4-67.9 34.9-17.5 19.8-27.8 44.3-25.6 71.9 26.1 2 49.9-11.4 69.5-34.3z'/%3E%3C/svg%3E" },
    { name: "Netflix", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Netflix_2015_logo.svg/200px-Netflix_2015_logo.svg.png" },
    { name: "Uber", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Uber_logo_2018.svg/200px-Uber_logo_2018.svg.png" },
    { name: "Airbnb", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Airbnb_Logo_B%C3%A9lo.svg/200px-Airbnb_Logo_B%C3%A9lo.svg.png" },
    { name: "Shopify", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Shopify_logo_2018.svg/200px-Shopify_logo_2018.svg.png" },
    { name: "Stripe", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Stripe_Logo%2C_revised_2016.svg/200px-Stripe_Logo%2C_revised_2016.svg.png" },
    { name: "Slack", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/Slack_icon_2019.svg/100px-Slack_icon_2019.svg.png" },
    { name: "Salesforce", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Salesforce.com_logo.svg/200px-Salesforce.com_logo.svg.png" },
    { name: "Adobe", logo: "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Adobe_Corporate_Logo.svg/150px-Adobe_Corporate_Logo.svg.png" },
  ];

  return (
    <div className="min-h-screen bg-white relative overflow-hidden">
      <div className="hero-glow" />

      {/* Header */}
      <header className="relative z-10 border-b border-gray-100">
        <nav className="max-w-6xl mx-auto px-6 flex items-center justify-between h-14">
          <div className="flex items-center gap-1">
            <div className="relative leading-tight">
              <div className="flex items-center">
                <span className="text-base font-bold text-gray-900 tracking-tight">MyCareer</span>
                <svg className="w-3 h-3 text-gray-400 ml-0.5 -mt-0.5 -rotate-45" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M21 16v-2l-8-5V3.5A1.5 1.5 0 0 0 11.5 2A1.5 1.5 0 0 0 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z" />
                </svg>
              </div>
              <div className="flex items-center -mt-1">
                <svg className="w-2.5 h-3 text-indigo-400 -mr-0.5 flex-shrink-0" viewBox="0 0 12 20" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M11 1C6 1 2 4 2 8C2 12 6 14 6 14" />
                </svg>
                <span className="text-base font-bold text-indigo-500 tracking-tight">CoPilot</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate('/how-it-works')}
              className="text-sm text-gray-500 hover:text-gray-900 px-3 py-1.5 rounded-md transition-colors duration-200 hidden sm:inline-flex"
            >
              How It Works
            </button>
            <Button
              data-testid="header-signin-btn"
              onClick={() => navigate(isLoggedIn ? '/dashboard' : '/auth')}
              className="bg-indigo-500 hover:bg-indigo-600 text-white h-8 px-4 text-sm font-medium rounded-lg transition-all duration-200"
            >
              {isLoggedIn ? (
                <><LayoutDashboard className="w-3.5 h-3.5 mr-1.5" />Dashboard</>
              ) : (
                "Sign In"
              )}
            </Button>
          </div>
        </nav>
      </header>

      {/* Hero */}
      <main className="relative z-10">
        <div className="max-w-4xl mx-auto px-6 pt-20 pb-16 text-center">
          <div className="space-y-6 animate-fade-in">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-50 border border-indigo-100">
              <Target className="w-3.5 h-3.5 text-indigo-500" />
              <span className="text-xs font-medium text-indigo-600">Quality-First Job Applications</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-[1.1] text-gray-900 tracking-tight">
              Apply to the right jobs —{" "}
              <span className="text-gradient">not every job</span>
            </h1>

            <p className="text-base sm:text-lg text-gray-500 max-w-2xl mx-auto leading-relaxed">
              A quality-first job application platform that finds strong matches, explains why they fit,
              and lets you approve every application before it's sent.
            </p>

            <p className="text-sm font-medium text-gray-900">
              No resume spam. No blind auto-apply. No burned opportunities.
            </p>

            <div className="flex flex-col sm:flex-row gap-3 justify-center items-center pt-2">
              <Button
                data-testid="get-started-btn"
                onClick={() => navigate(isLoggedIn ? '/dashboard' : '/auth')}
                className="bg-indigo-500 hover:bg-indigo-600 text-white btn-glow group h-11 px-6 text-sm font-medium rounded-lg transition-all duration-200"
              >
                {isLoggedIn ? "Go to Dashboard" : "Find jobs that actually fit me"}
                <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-0.5 transition-transform duration-200" />
              </Button>
              <button
                data-testid="learn-more-btn"
                className="text-sm font-medium text-gray-500 hover:text-indigo-600 px-4 py-2 transition-colors duration-200"
                onClick={() => navigate('/how-it-works')}
              >
                See how it works →
              </button>
            </div>
          </div>
        </div>

        {/* Metrics */}
        <section className="max-w-4xl mx-auto px-6 pb-16">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {metrics.map((m, i) => (
              <div key={i} className="bg-white border border-gray-200 rounded-xl p-5 text-center transition-all duration-200 hover:border-gray-300 hover:shadow-sm">
                <m.icon className="w-5 h-5 text-indigo-500 mx-auto mb-2" />
                <p className="text-lg font-bold text-gray-900">{m.value}</p>
                <p className="text-xs text-gray-500 mt-1">{m.label}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Logo Carousel */}
        <section className="max-w-5xl mx-auto pb-16 overflow-hidden">
          <p className="text-center text-xs text-gray-400 mb-6 font-medium uppercase tracking-wider">
            Works with applications at top companies
          </p>
          <div className="relative">
            <div className="absolute left-0 top-0 bottom-0 w-16 bg-gradient-to-r from-white to-transparent z-10" />
            <div className="absolute right-0 top-0 bottom-0 w-16 bg-gradient-to-l from-white to-transparent z-10" />
            <div className="flex animate-scroll">
              {[0, 1].map((set) => (
                <div key={set} className="flex items-center gap-14 px-8 shrink-0">
                  {logos.map((c, i) => (
                    <div key={`logo-${set}-${i}`} className="flex items-center justify-center h-8 opacity-70 hover:opacity-100 transition-opacity duration-300">
                      <img src={c.logo} alt={c.name} className="h-6 w-auto object-contain" loading="lazy" />
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="max-w-5xl mx-auto px-6 py-20">
          <div className="text-center mb-12 animate-fade-in">
            <div className="inline-flex items-center gap-2 bg-indigo-50 text-indigo-600 px-3 py-1.5 rounded-full text-xs font-medium mb-4">
              <Chrome className="w-3.5 h-3.5" />
              Chrome Extension
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-3 tracking-tight">
              Apply to jobs in seconds, not hours
            </h2>
            <p className="text-sm sm:text-base text-gray-500 max-w-xl mx-auto">
              Our Chrome extension lives right where you job hunt.{" "}
              <span className="text-gray-900 font-medium">Find a job. Click. Apply. Done.</span>
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            {features.map((f, i) => (
              <div
                key={i}
                data-testid={`feature-card-${i}`}
                className="bg-white border border-gray-200 rounded-xl p-6 transition-all duration-200 hover:border-gray-300 hover:shadow-sm group"
              >
                <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-500 mb-4 group-hover:bg-indigo-100 transition-colors duration-200">
                  <f.icon className="w-5 h-5" />
                </div>
                <h3 className="text-base font-semibold text-gray-900 mb-2">{f.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed mb-3">{f.description}</p>
                <p className="text-xs font-medium text-gray-700 pt-3 border-t border-gray-100">
                  {f.highlight}
                </p>
              </div>
            ))}
          </div>

          {/* Steps */}
          <div className="mt-20">
            <h3 className="text-xl font-bold text-gray-900 text-center mb-10 tracking-tight">How it works</h3>
            <div className="grid md:grid-cols-4 gap-6">
              {steps.map((s, i) => (
                <div key={i} className="text-center">
                  <div className={`w-10 h-10 rounded-full ${s.color} flex items-center justify-center mx-auto mb-3 text-sm font-bold`}>
                    {s.num}
                  </div>
                  <h4 className="text-sm font-semibold text-gray-900 mb-1">{s.title}</h4>
                  <p className="text-xs text-gray-500 leading-relaxed">{s.desc}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="text-center mt-10">
            <Button
              className="bg-indigo-500 hover:bg-indigo-600 text-white px-6 h-10 text-sm font-medium rounded-lg shadow-sm transition-all duration-200"
              onClick={() => window.open('/api/public/extension/download', '_blank')}
            >
              <Download className="w-4 h-4 mr-2" />
              Download Chrome Extension
            </Button>
            <p className="text-xs text-gray-400 mt-2">Free forever. No credit card required.</p>
          </div>
        </section>

        {/* Reviews */}
        <section className="max-w-5xl mx-auto px-6 py-20">
          <div className="text-center mb-10">
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2 tracking-tight">What our users are saying</h2>
            <p className="text-sm text-gray-500">Real results from job seekers using the extension</p>
          </div>
          <div className="grid md:grid-cols-3 gap-4">
            {reviews.map((r, i) => (
              <div key={i} data-testid={`review-${i + 1}`} className="bg-white border border-gray-200 rounded-xl p-5 transition-all duration-200 hover:border-gray-300 hover:shadow-sm">
                <div className="flex gap-0.5 mb-3">
                  {[...Array(5)].map((_, j) => (
                    <svg key={j} className="w-4 h-4 text-amber-400 fill-current" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  ))}
                </div>
                <p className="text-sm text-gray-600 leading-relaxed mb-4 italic">"{r.text}"</p>
                <div className="pt-3 border-t border-gray-100">
                  <p className="text-sm font-medium text-gray-900">{r.name}</p>
                  <p className="text-xs text-gray-500">{r.role} &middot; {r.loc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Skip Section */}
        <section className="max-w-3xl mx-auto px-6 py-20">
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
            <div className="p-8 sm:p-10">
              <div className="flex items-start gap-3 mb-5">
                <div className="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center flex-shrink-0">
                  <AlertTriangle className="w-5 h-5 text-amber-600" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900 mb-1 tracking-tight">Why We Skip Jobs On Purpose</h2>
                  <p className="text-sm text-gray-500">Applying to the wrong job can hurt your chances at a company forever.</p>
                </div>
              </div>
              <p className="text-sm text-gray-700 mb-4 font-medium">That's why we:</p>
              <div className="grid sm:grid-cols-2 gap-2 mb-6">
                {skipReasons.map((reason, i) => (
                  <div key={i} className="flex items-center gap-2.5 p-2.5 rounded-lg bg-gray-50">
                    <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                    <span className="text-sm text-gray-700">{reason}</span>
                  </div>
                ))}
              </div>
              <p className="text-sm font-semibold text-gray-900 text-center pt-4 border-t border-gray-100">
                Skipping is not failure — it's strategy.
              </p>
            </div>
          </div>
        </section>

        {/* Trust Badges */}
        <section className="max-w-4xl mx-auto px-6 py-12">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {trustBadges.map((b, i) => (
              <div key={i} className="flex flex-col items-center text-center p-3">
                <div className="w-10 h-10 rounded-full bg-gray-50 border border-gray-200 flex items-center justify-center mb-2">
                  <b.icon className="w-4 h-4 text-gray-500" />
                </div>
                <p className="text-xs font-medium text-gray-700">{b.label}</p>
              </div>
            ))}
          </div>
          <p className="text-center text-xs text-gray-400 mt-4">
            Built for candidates who care about long-term career outcomes.
          </p>
        </section>

        {/* Final CTA */}
        <section className="max-w-3xl mx-auto px-6 py-20">
          <div className="bg-gray-900 rounded-2xl p-10 sm:p-12 text-center">
            <h2 className="text-2xl sm:text-3xl font-bold text-white mb-2 tracking-tight">Stop applying blindly.</h2>
            <p className="text-xl text-gray-300 font-medium mb-4">Start applying intentionally.</p>
            <p className="text-sm text-gray-400 max-w-md mx-auto mb-6">
              Review fewer jobs. Send better applications. Get more interviews.
            </p>
            <Button
              data-testid="cta-get-started-btn"
              onClick={() => navigate(isLoggedIn ? '/dashboard' : '/auth')}
              className="bg-indigo-500 hover:bg-indigo-400 text-white h-11 px-8 text-sm font-medium rounded-lg transition-all duration-200"
            >
              {isLoggedIn ? "Go to Dashboard" : "Find jobs that actually fit me"}
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-gray-100 bg-white">
        <div className="max-w-6xl mx-auto px-6 py-6 flex flex-col md:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-indigo-500 flex items-center justify-center">
              <Sparkles className="w-3 h-3 text-white" />
            </div>
            <span className="text-xs text-gray-400">&copy; 2025 MyCareerCoPilot. All rights reserved.</span>
          </div>
          <div className="flex items-center gap-5">
            <a href="#" className="text-xs text-gray-400 hover:text-gray-600 transition-colors duration-200">Privacy</a>
            <a href="#" className="text-xs text-gray-400 hover:text-gray-600 transition-colors duration-200">Terms</a>
            <Link to="/support" className="text-xs text-gray-400 hover:text-gray-600 transition-colors duration-200">Support</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
