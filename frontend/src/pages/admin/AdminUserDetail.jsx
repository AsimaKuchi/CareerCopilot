import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Crown,
  Ban,
  Lock,
  KeyRound,
  Mail,
  Calendar,
  Briefcase,
  Bookmark,
} from "lucide-react";
import { apiFetch } from "../../utils/apiFetch";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL;

const FEATURE_LABELS = {
  job_applications: "Job Applications",
  resume_optimizations: "Resume Optimizations",
  interview_prep: "Interview Prep",
  career_paths: "Career Paths",
  cover_letters: "Cover Letters",
  extension_uses: "Extension Uses",
};

export default function AdminUserDetail() {
  const { userId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchDetail = () => {
    setLoading(true);
    fetch(`${API}/api/admin/users/${userId}`, { credentials: "include" })
      .then((r) => r.json())
      .then(setData)
      .catch(() => toast.error("Failed to load user"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchDetail();
  }, [userId]);

  const handleBan = async () => {
    if (!window.confirm("Ban this user?")) return;
    setActionLoading(true);
    try {
      await apiFetch(`${API}/api/admin/users/${userId}/ban`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ reason: "Admin action" }),
      });
      toast.success("User banned");
      fetchDetail();
    } catch {
      toast.error("Failed");
    }
    setActionLoading(false);
  };

  const handleUnban = async () => {
    setActionLoading(true);
    try {
      await apiFetch(`${API}/api/admin/users/${userId}/unban`, {
        method: "POST",
        credentials: "include",
      });
      toast.success("User unbanned");
      fetchDetail();
    } catch {
      toast.error("Failed");
    }
    setActionLoading(false);
  };

  const handleUnlock = async () => {
    setActionLoading(true);
    try {
      await apiFetch(`${API}/api/admin/users/${userId}/unlock`, {
        method: "POST",
        credentials: "include",
      });
      toast.success("Unlocked");
      fetchDetail();
    } catch {
      toast.error("Failed");
    }
    setActionLoading(false);
  };

  const handleResetPassword = async () => {
    if (!window.confirm("Reset this user's password? A temporary password will be generated."))
      return;
    setActionLoading(true);
    try {
      const res = await apiFetch(`${API}/api/admin/users/${userId}/reset-password`, {
        method: "POST",
        credentials: "include",
      });
      const result = await res.json();
      toast.success(`Temp password: ${result.temp_password}`, { duration: 15000 });
    } catch {
      toast.error("Failed");
    }
    setActionLoading(false);
  };

  const handleSubscriptionOverride = async (plan) => {
    setActionLoading(true);
    try {
      await apiFetch(`${API}/api/admin/users/${userId}/subscription`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ plan }),
      });
      toast.success(`Set to ${plan}`);
      fetchDetail();
    } catch {
      toast.error("Failed");
    }
    setActionLoading(false);
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="w-6 h-6 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!data) return <div className="p-8 text-gray-400">User not found</div>;

  const { user, profile, usage, app_count, saved_jobs_count, recent_activity } = data;
  const isPro = user.subscription_status === "active";
  const isBanned = user.banned;
  const isLocked = (user.failed_login_attempts || 0) >= 5;

  return (
    <div className="p-8 max-w-4xl" data-testid="admin-user-detail">
      <button
        onClick={() => navigate("/admin/users")}
        className="flex items-center gap-2 text-sm text-gray-400 hover:text-white mb-6"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Users
      </button>

      {/* User Header */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              {user.name || "No name"}
              {isPro && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-indigo-500/20 text-indigo-400">
                  <Crown className="w-3 h-3" /> Pro
                </span>
              )}
              {isBanned && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-red-500/20 text-red-400">
                  <Ban className="w-3 h-3" /> Banned
                </span>
              )}
              {isLocked && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-amber-500/20 text-amber-400">
                  <Lock className="w-3 h-3" /> Locked
                </span>
              )}
            </h1>
            <div className="flex items-center gap-4 mt-2 text-sm text-gray-400">
              <span className="flex items-center gap-1">
                <Mail className="w-3.5 h-3.5" /> {user.email}
              </span>
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5" />{" "}
                Joined {user.created_at ? new Date(user.created_at).toLocaleDateString() : "—"}
              </span>
            </div>
          </div>
          <span className="text-xs px-2 py-1 rounded bg-gray-800 text-gray-400">{user.role}</span>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-gray-800">
          {isBanned ? (
            <button onClick={handleUnban} disabled={actionLoading}
              className="px-3 py-1.5 text-sm rounded-lg bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30">
              Unban
            </button>
          ) : user.role !== "admin" && (
            <button onClick={handleBan} disabled={actionLoading}
              className="px-3 py-1.5 text-sm rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30">
              Ban User
            </button>
          )}
          {isLocked && (
            <button onClick={handleUnlock} disabled={actionLoading}
              className="px-3 py-1.5 text-sm rounded-lg bg-amber-500/20 text-amber-400 hover:bg-amber-500/30">
              Unlock Account
            </button>
          )}
          <button onClick={handleResetPassword} disabled={actionLoading}
            className="px-3 py-1.5 text-sm rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 flex items-center gap-1">
            <KeyRound className="w-3.5 h-3.5" /> Reset Password
          </button>
          {isPro ? (
            <button onClick={() => handleSubscriptionOverride("free")} disabled={actionLoading}
              className="px-3 py-1.5 text-sm rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700">
              Downgrade to Free
            </button>
          ) : (
            <button onClick={() => handleSubscriptionOverride("pro")} disabled={actionLoading}
              className="px-3 py-1.5 text-sm rounded-lg bg-indigo-500/20 text-indigo-400 hover:bg-indigo-500/30 flex items-center gap-1">
              <Crown className="w-3.5 h-3.5" /> Upgrade to Pro
            </button>
          )}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
          <Briefcase className="w-4 h-4 text-gray-500 mb-2" />
          <p className="text-lg font-bold text-white">{app_count}</p>
          <p className="text-xs text-gray-500">Applications</p>
        </div>
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
          <Bookmark className="w-4 h-4 text-gray-500 mb-2" />
          <p className="text-lg font-bold text-white">{saved_jobs_count}</p>
          <p className="text-xs text-gray-500">Saved Jobs</p>
        </div>
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
          <p className="text-xs text-gray-500 mb-2">Failed Logins</p>
          <p className="text-lg font-bold text-white">{user.failed_login_attempts || 0}</p>
        </div>
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
          <p className="text-xs text-gray-500 mb-2">Last Login</p>
          <p className="text-sm font-medium text-white">
            {user.last_login ? new Date(user.last_login).toLocaleString() : "Never"}
          </p>
        </div>
      </div>

      {/* Usage This Month */}
      {usage && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 mb-6">
          <h3 className="text-lg font-semibold text-white mb-4">Usage This Month</h3>
          <div className="grid sm:grid-cols-3 gap-3">
            {Object.entries(FEATURE_LABELS).map(([key, label]) => (
              <div key={key} className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
                <span className="text-sm text-gray-400">{label}</span>
                <span className="text-sm font-medium text-white">{usage[key] || 0}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Activity */}
      {recent_activity && recent_activity.length > 0 && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {recent_activity.map((log, i) => (
              <div key={i} className="flex items-center justify-between px-3 py-2 rounded-lg bg-gray-800/50">
                <div>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                    log.severity === "warning" ? "bg-amber-500/20 text-amber-400" :
                    log.type === "admin_action" ? "bg-indigo-500/20 text-indigo-400" :
                    "bg-gray-700 text-gray-400"
                  }`}>
                    {log.type}
                  </span>
                  <span className="text-sm text-gray-300 ml-2">{log.details || log.action || ""}</span>
                </div>
                <span className="text-xs text-gray-500">
                  {log.timestamp ? new Date(log.timestamp).toLocaleString() : ""}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
