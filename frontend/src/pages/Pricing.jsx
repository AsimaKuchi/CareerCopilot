import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Check, Zap, Crown, ArrowRight, Shield } from "lucide-react";
import { apiFetch } from "../utils/apiFetch";
import { toast } from "sonner";
import Navbar from "../components/Navbar";

const API = process.env.REACT_APP_BACKEND_URL;

const FREE_FEATURES = [
  { name: "Job Applications", limit: "5 / month" },
  { name: "Resume Optimizations", limit: "5 / month" },
  { name: "Cover Letters", limit: "5 / month" },
  { name: "Interview Prep", limit: "3 / month" },
  { name: "Career Path Analysis", limit: "2 / month" },
  { name: "Chrome Extension Uses", limit: "5 / month" },
  { name: "Job Search", limit: "Unlimited" },
  { name: "Profile & Resume Upload", limit: "Unlimited" },
];

const PRO_FEATURES = [
  { name: "Job Applications", limit: "Unlimited" },
  { name: "Resume Optimizations", limit: "Unlimited" },
  { name: "Cover Letters", limit: "Unlimited" },
  { name: "Interview Prep", limit: "Unlimited" },
  { name: "Career Path Analysis", limit: "Unlimited" },
  { name: "Chrome Extension Uses", limit: "Unlimited" },
  { name: "Job Search", limit: "Unlimited" },
  { name: "Advanced Analytics", limit: "All-time data" },
  { name: "Priority Support", limit: "Included" },
  { name: "Export to PDF/Word", limit: "Included" },
  { name: "Premium Templates", limit: "Included" },
];

export default function Pricing() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [subscription, setSubscription] = useState(null);
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Check if logged in
    fetch(`${API}/api/auth/me`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data) {
          setUser(data);
          apiFetch(`${API}/api/subscription`, { credentials: "include" })
            .then((r) => r.json())
            .then(setSubscription)
            .catch(() => {});
        }
      })
      .catch(() => {});
  }, []);

  const isPro = subscription?.plan === "pro";

  const handleUpgrade = async () => {
    if (!user) {
      navigate("/auth");
      return;
    }
    setLoading(true);
    try {
      const origin = window.location.origin;
      const res = await apiFetch(`${API}/api/stripe/create-checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ origin_url: origin }),
      });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      } else {
        toast.error(data.detail || "Failed to start checkout");
      }
    } catch (err) {
      toast.error("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar user={user} />
      <div className="max-w-5xl mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-3" data-testid="pricing-title">
            Simple, Transparent Pricing
          </h1>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto">
            Try every feature for free. Upgrade when you're ready to go unlimited.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {/* Free Tier */}
          <div
            className="bg-white rounded-2xl border border-gray-200 p-8 flex flex-col"
            data-testid="free-plan-card"
          >
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center">
                <Zap className="w-5 h-5 text-gray-600" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900">Free</h2>
            </div>
            <div className="mt-4 mb-6">
              <span className="text-4xl font-bold text-gray-900">$0</span>
              <span className="text-gray-500 ml-1">/month</span>
            </div>
            <p className="text-gray-500 text-sm mb-6">
              Try all features with monthly limits. No credit card required.
            </p>
            <ul className="space-y-3 mb-8 flex-1">
              {FREE_FEATURES.map((f) => (
                <li key={f.name} className="flex items-start gap-3 text-sm">
                  <Check className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
                  <span className="text-gray-700">
                    {f.name}{" "}
                    <span className="text-gray-400">({f.limit})</span>
                  </span>
                </li>
              ))}
            </ul>
            {!user ? (
              <button
                onClick={() => navigate("/auth")}
                className="w-full py-3 rounded-xl border border-gray-300 text-gray-700 font-medium hover:bg-gray-50 transition-colors"
                data-testid="free-plan-signup-btn"
              >
                Get Started Free
              </button>
            ) : (
              <div className="w-full py-3 rounded-xl bg-gray-100 text-gray-500 font-medium text-center">
                {isPro ? "Previous Plan" : "Current Plan"}
              </div>
            )}
          </div>

          {/* Pro Tier */}
          <div
            className="bg-white rounded-2xl border-2 border-indigo-500 p-8 flex flex-col relative"
            data-testid="pro-plan-card"
          >
            <div className="absolute -top-3 right-6 bg-indigo-500 text-white text-xs font-semibold px-3 py-1 rounded-full">
              RECOMMENDED
            </div>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-xl bg-indigo-100 flex items-center justify-center">
                <Crown className="w-5 h-5 text-indigo-600" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900">Pro</h2>
            </div>
            <div className="mt-4 mb-6">
              <span className="text-4xl font-bold text-gray-900">$19.99</span>
              <span className="text-gray-500 ml-1">/month</span>
            </div>
            <p className="text-gray-500 text-sm mb-6">
              Unlimited access to every feature. Cancel anytime.
            </p>
            <ul className="space-y-3 mb-8 flex-1">
              {PRO_FEATURES.map((f) => (
                <li key={f.name} className="flex items-start gap-3 text-sm">
                  <Check className="w-4 h-4 text-indigo-500 mt-0.5 shrink-0" />
                  <span className="text-gray-700">
                    {f.name}{" "}
                    <span className="text-gray-400">({f.limit})</span>
                  </span>
                </li>
              ))}
            </ul>
            {isPro ? (
              <div className="w-full py-3 rounded-xl bg-indigo-100 text-indigo-600 font-medium text-center">
                Current Plan
              </div>
            ) : (
              <button
                onClick={handleUpgrade}
                disabled={loading}
                className="w-full py-3 rounded-xl bg-indigo-600 text-white font-medium hover:bg-indigo-700 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                data-testid="upgrade-pro-btn"
              >
                {loading ? (
                  "Redirecting to checkout..."
                ) : (
                  <>
                    Upgrade to Pro <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        {/* Trust badges */}
        <div className="mt-12 flex flex-wrap items-center justify-center gap-6 text-sm text-gray-400">
          <div className="flex items-center gap-1.5">
            <Shield className="w-4 h-4" />
            <span>Secure payments via Stripe</span>
          </div>
          <span>Cancel anytime</span>
          <span>No hidden fees</span>
        </div>
      </div>
    </div>
  );
}
