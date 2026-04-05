import { useState, useEffect } from "react";
import {
  ShieldAlert,
  Lock,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";
import { apiFetch } from "../../utils/apiFetch";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL;

export default function AdminSecurity() {
  const [summary, setSummary] = useState(null);
  const [lockouts, setLockouts] = useState([]);
  const [failedLogins, setFailedLogins] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [sumRes, lockRes, failRes] = await Promise.all([
        fetch(`${API}/api/admin/security/summary`, { credentials: "include" }),
        fetch(`${API}/api/admin/security/lockouts`, { credentials: "include" }),
        fetch(`${API}/api/admin/security/failed-logins?limit=30`, { credentials: "include" }),
      ]);
      const [sumData, lockData, failData] = await Promise.all([
        sumRes.json(),
        lockRes.json(),
        failRes.json(),
      ]);
      setSummary(sumData);
      setLockouts(lockData.locked_accounts || []);
      setFailedLogins(failData.logs || []);
    } catch {
      toast.error("Failed to load security data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleUnlock = async (userId) => {
    try {
      await apiFetch(`${API}/api/admin/users/${userId}/unlock`, {
        method: "POST",
        credentials: "include",
      });
      toast.success("Account unlocked");
      fetchData();
    } catch {
      toast.error("Failed to unlock");
    }
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="w-6 h-6 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-8" data-testid="admin-security">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Security Monitoring</h1>
        <button
          onClick={fetchData}
          className="flex items-center gap-2 px-3 py-2 bg-gray-800 text-gray-300 rounded-lg text-sm hover:bg-gray-700"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
            <ShieldAlert className="w-5 h-5 text-red-400 mb-2" />
            <p className="text-2xl font-bold text-white">{summary.failed_logins_24h}</p>
            <p className="text-sm text-gray-500">Failed Logins (24h)</p>
          </div>
          <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
            <AlertTriangle className="w-5 h-5 text-amber-400 mb-2" />
            <p className="text-2xl font-bold text-white">{summary.failed_logins_7d}</p>
            <p className="text-sm text-gray-500">Failed Logins (7d)</p>
          </div>
          <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
            <Lock className="w-5 h-5 text-amber-400 mb-2" />
            <p className="text-2xl font-bold text-white">{summary.locked_accounts}</p>
            <p className="text-sm text-gray-500">Locked Accounts</p>
          </div>
          <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
            <div className="w-5 h-5 rounded-full bg-red-500/20 flex items-center justify-center mb-2">
              <span className="text-xs text-red-400 font-bold">!</span>
            </div>
            <p className="text-2xl font-bold text-white">{summary.banned_users}</p>
            <p className="text-sm text-gray-500">Banned Users</p>
          </div>
        </div>
      )}

      {/* Top Offending IPs */}
      {summary?.top_offending_ips?.length > 0 && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 mb-6">
          <h3 className="text-lg font-semibold text-white mb-4">Top Offending IPs (24h)</h3>
          <div className="space-y-2">
            {summary.top_offending_ips.map((item, i) => (
              <div key={i} className="flex items-center justify-between px-3 py-2 bg-gray-800 rounded-lg">
                <code className="text-sm text-gray-300 font-mono">{item.ip}</code>
                <span className="text-sm font-medium text-red-400">{item.count} attempts</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Locked Accounts */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 mb-6">
        <h3 className="text-lg font-semibold text-white mb-4">
          Locked Accounts ({lockouts.length})
        </h3>
        {lockouts.length === 0 ? (
          <p className="text-gray-500 text-sm">No accounts currently locked</p>
        ) : (
          <div className="space-y-2">
            {lockouts.map((u) => (
              <div key={u.user_id} className="flex items-center justify-between px-3 py-2 bg-gray-800 rounded-lg">
                <div>
                  <p className="text-sm text-white">{u.email}</p>
                  <p className="text-xs text-gray-500">
                    {u.failed_login_attempts} failed attempts
                  </p>
                </div>
                <button
                  onClick={() => handleUnlock(u.user_id)}
                  className="px-3 py-1 text-xs rounded-lg bg-amber-500/20 text-amber-400 hover:bg-amber-500/30"
                >
                  Unlock
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Failed Logins */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Failed Logins</h3>
        {failedLogins.length === 0 ? (
          <p className="text-gray-500 text-sm">No recent failed login attempts</p>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {failedLogins.map((log, i) => (
              <div key={i} className="flex items-center justify-between px-3 py-2 bg-gray-800/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <ShieldAlert className="w-4 h-4 text-red-400" />
                  <div>
                    <p className="text-sm text-white">{log.user_email}</p>
                    <p className="text-xs text-gray-500">{log.details}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500">
                    {log.timestamp ? new Date(log.timestamp).toLocaleString() : ""}
                  </p>
                  {log.ip_address && (
                    <p className="text-xs text-gray-600 font-mono">{log.ip_address}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
