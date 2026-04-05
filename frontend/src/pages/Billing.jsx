import { useState, useEffect, useCallback } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import {
  Crown,
  CreditCard,
  FileText,
  ExternalLink,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
} from "lucide-react";
import { apiFetch } from "../utils/apiFetch";
import { toast } from "sonner";
import Navbar from "../components/Navbar";

const API = process.env.REACT_APP_BACKEND_URL;

const FEATURE_LABELS = {
  job_applications: "Job Applications",
  resume_optimizations: "Resume Optimizations",
  interview_prep: "Interview Prep Sessions",
  career_paths: "Career Path Analysis",
  cover_letters: "Cover Letter Generation",
  extension_uses: "Chrome Extension Uses",
};

export default function Billing({ user }) {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [subscription, setSubscription] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [pollCount, setPollCount] = useState(0);

  const sessionId = searchParams.get("session_id");

  const fetchSubscription = useCallback(async () => {
    try {
      const res = await apiFetch(`${API}/api/subscription`, {
        credentials: "include",
      });
      const data = await res.json();
      setSubscription(data);
      return data;
    } catch {
      return null;
    }
  }, []);

  const fetchInvoices = useCallback(async () => {
    try {
      const res = await apiFetch(`${API}/api/subscription/invoices`, {
        credentials: "include",
      });
      const data = await res.json();
      setInvoices(data.invoices || []);
    } catch {
      // ignore
    }
  }, []);

  // Poll payment status after checkout redirect
  useEffect(() => {
    if (!sessionId || pollCount >= 5) return;

    const poll = async () => {
      try {
        const res = await apiFetch(
          `${API}/api/stripe/checkout-status/${sessionId}`,
          { credentials: "include" }
        );
        const data = await res.json();

        if (data.payment_status === "paid") {
          toast.success("Payment successful! Welcome to Pro!");
          fetchSubscription();
          fetchInvoices();
          // Clear session_id from URL
          navigate("/billing", { replace: true });
          return;
        }
        if (data.status === "expired") {
          toast.error("Payment session expired. Please try again.");
          navigate("/billing", { replace: true });
          return;
        }
      } catch {
        // continue polling
      }
      setPollCount((c) => c + 1);
    };

    const timer = setTimeout(poll, pollCount === 0 ? 500 : 2000);
    return () => clearTimeout(timer);
  }, [sessionId, pollCount, fetchSubscription, fetchInvoices, navigate]);

  useEffect(() => {
    Promise.all([fetchSubscription(), fetchInvoices()]).finally(() =>
      setLoading(false)
    );
  }, [fetchSubscription, fetchInvoices]);

  const isPro = subscription?.plan === "pro";
  const isCancelling = subscription?.cancel_at_period_end;

  const handleCancel = async () => {
    if (!window.confirm("Are you sure you want to cancel? You'll keep access until the end of your billing period."))
      return;
    setActionLoading(true);
    try {
      const res = await apiFetch(`${API}/api/subscription/cancel`, {
        method: "POST",
        credentials: "include",
      });
      const data = await res.json();
      toast.success(data.message);
      fetchSubscription();
    } catch {
      toast.error("Failed to cancel subscription");
    } finally {
      setActionLoading(false);
    }
  };

  const handleReactivate = async () => {
    setActionLoading(true);
    try {
      const res = await apiFetch(`${API}/api/subscription/reactivate`, {
        method: "POST",
        credentials: "include",
      });
      const data = await res.json();
      toast.success(data.message);
      fetchSubscription();
    } catch {
      toast.error("Failed to reactivate subscription");
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdatePayment = async () => {
    setActionLoading(true);
    try {
      const origin = window.location.origin;
      const res = await apiFetch(`${API}/api/subscription/update-payment`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ origin_url: origin }),
      });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      }
    } catch {
      toast.error("Failed to open billing portal");
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar user={user} />
        <div className="flex items-center justify-center py-32">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar user={user} />
      <div className="max-w-4xl mx-auto px-4 py-12">
        <h1 className="text-3xl font-bold text-gray-900 mb-8" data-testid="billing-title">
          Billing & Subscription
        </h1>

        {/* Polling indicator */}
        {sessionId && pollCount < 5 && (
          <div className="mb-6 p-4 bg-indigo-50 border border-indigo-200 rounded-xl flex items-center gap-3">
            <Loader2 className="w-5 h-5 animate-spin text-indigo-500" />
            <span className="text-indigo-700 font-medium">
              Verifying your payment...
            </span>
          </div>
        )}

        {/* Current Plan Card */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-6" data-testid="current-plan-card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                  isPro ? "bg-indigo-100" : "bg-gray-100"
                }`}
              >
                <Crown
                  className={`w-5 h-5 ${
                    isPro ? "text-indigo-600" : "text-gray-500"
                  }`}
                />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">
                  {isPro ? "Pro Plan" : "Free Plan"}
                </h2>
                <p className="text-sm text-gray-500">
                  {isPro
                    ? isCancelling
                      ? `Cancels on ${new Date(subscription.current_period_end).toLocaleDateString()}`
                      : `Renews on ${new Date(subscription.current_period_end).toLocaleDateString()}`
                    : "Try all features with monthly limits"}
                </p>
              </div>
            </div>
            {isPro && (
              <span className="text-2xl font-bold text-gray-900">
                $19.99<span className="text-sm font-normal text-gray-500">/mo</span>
              </span>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-3 flex-wrap">
            {isPro ? (
              <>
                <button
                  onClick={handleUpdatePayment}
                  disabled={actionLoading}
                  className="px-4 py-2 text-sm rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                  data-testid="update-payment-btn"
                >
                  <CreditCard className="w-4 h-4" />
                  Update Payment Method
                </button>
                {isCancelling ? (
                  <button
                    onClick={handleReactivate}
                    disabled={actionLoading}
                    className="px-4 py-2 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 flex items-center gap-2"
                    data-testid="reactivate-btn"
                  >
                    Reactivate Subscription
                  </button>
                ) : (
                  <button
                    onClick={handleCancel}
                    disabled={actionLoading}
                    className="px-4 py-2 text-sm rounded-lg border border-red-200 text-red-600 hover:bg-red-50"
                    data-testid="cancel-subscription-btn"
                  >
                    Cancel Subscription
                  </button>
                )}
              </>
            ) : (
              <button
                onClick={() => navigate("/pricing")}
                className="px-4 py-2 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 flex items-center gap-2"
                data-testid="upgrade-from-billing-btn"
              >
                <Crown className="w-4 h-4" />
                Upgrade to Pro
              </button>
            )}
          </div>
        </div>

        {/* Usage Card */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-6" data-testid="usage-card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Monthly Usage
          </h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {subscription?.usage &&
              Object.entries(subscription.usage).map(([key, val]) => {
                const isUnlimited = val.limit === -1;
                const pct = isUnlimited
                  ? 0
                  : Math.min(100, (val.current / val.limit) * 100);
                const isNearLimit = !isUnlimited && pct >= 80;
                const isAtLimit = !isUnlimited && val.current >= val.limit;

                return (
                  <div key={key} className="p-3 rounded-xl bg-gray-50">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">
                        {FEATURE_LABELS[key] || key}
                      </span>
                      {isAtLimit && (
                        <AlertTriangle className="w-4 h-4 text-amber-500" />
                      )}
                    </div>
                    <div className="text-lg font-semibold text-gray-900">
                      {isUnlimited ? (
                        <span className="text-indigo-600">Unlimited</span>
                      ) : (
                        `${val.current} / ${val.limit}`
                      )}
                    </div>
                    {!isUnlimited && (
                      <div className="mt-2 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            isAtLimit
                              ? "bg-red-500"
                              : isNearLimit
                              ? "bg-amber-500"
                              : "bg-indigo-500"
                          }`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    )}
                  </div>
                );
              })}
          </div>
        </div>

        {/* Invoices */}
        {invoices.length > 0 && (
          <div className="bg-white rounded-2xl border border-gray-200 p-6" data-testid="invoices-card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Payment History
            </h3>
            <div className="divide-y divide-gray-100">
              {invoices.map((inv) => (
                <div
                  key={inv.id}
                  className="flex items-center justify-between py-3"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="w-4 h-4 text-gray-400" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        ${inv.amount.toFixed(2)} {inv.currency.toUpperCase()}
                      </p>
                      <p className="text-xs text-gray-500">
                        {new Date(inv.created).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {inv.status === "paid" ? (
                      <CheckCircle2 className="w-4 h-4 text-green-500" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-500" />
                    )}
                    {inv.invoice_url && (
                      <a
                        href={inv.invoice_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-indigo-600 hover:text-indigo-700"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
