import { useState, useEffect } from "react";
import {
  Users,
  DollarSign,
  Activity,
  ShieldAlert,
  Briefcase,
  TrendingUp,
  UserPlus,
  Database,
} from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL;

function StatCard({ icon: Icon, label, value, sub, color = "indigo" }) {
  const colors = {
    indigo: "bg-indigo-500/10 text-indigo-400",
    green: "bg-emerald-500/10 text-emerald-400",
    amber: "bg-amber-500/10 text-amber-400",
    red: "bg-red-500/10 text-red-400",
    blue: "bg-blue-500/10 text-blue-400",
  };

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
      <div className="flex items-center justify-between mb-3">
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${colors[color]}`}>
          <Icon className="w-4 h-4" />
        </div>
        {sub && <span className="text-xs text-gray-500">{sub}</span>}
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className="text-sm text-gray-500 mt-1">{label}</p>
    </div>
  );
}

export default function AdminOverview() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/admin/overview`, { credentials: "include" })
      .then((r) => r.json())
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="w-6 h-6 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!stats) {
    return <div className="p-8 text-gray-400">Failed to load stats</div>;
  }

  const usage = stats.usage_this_month || {};

  return (
    <div className="p-8" data-testid="admin-overview">
      <h1 className="text-2xl font-bold text-white mb-6">Dashboard Overview</h1>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard icon={Users} label="Total Users" value={stats.total_users} color="indigo" />
        <StatCard icon={DollarSign} label="Monthly Revenue" value={`$${stats.mrr}`} sub={`${stats.pro_users} Pro`} color="green" />
        <StatCard icon={Activity} label="Active (24h)" value={stats.active_users_24h} color="blue" />
        <StatCard icon={ShieldAlert} label="Failed Logins (24h)" value={stats.failed_logins_24h} sub={`${stats.locked_accounts} locked`} color="red" />
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard icon={Briefcase} label="Applications Today" value={stats.apps_today} color="amber" />
        <StatCard icon={UserPlus} label="Signups Today" value={stats.signups_today} sub={`${stats.signups_7d} this week`} color="indigo" />
        <StatCard icon={TrendingUp} label="Signups (30d)" value={stats.signups_30d} color="green" />
        <StatCard icon={Database} label="Jobs Indexed" value={stats.total_jobs_indexed?.toLocaleString()} color="blue" />
      </div>

      {/* User Breakdown */}
      <div className="grid lg:grid-cols-2 gap-6">
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">User Breakdown</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Free Users</span>
              <span className="text-white font-medium">{stats.free_users}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Pro Users</span>
              <span className="text-indigo-400 font-medium">{stats.pro_users}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Conversion Rate</span>
              <span className="text-emerald-400 font-medium">
                {stats.total_users > 0
                  ? `${((stats.pro_users / stats.total_users) * 100).toFixed(1)}%`
                  : "0%"}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Feature Usage (This Month)</h3>
          <div className="space-y-3">
            {[
              ["Resume Optimizations", usage.total_resume_opts || 0],
              ["Cover Letters", usage.total_cover_letters || 0],
              ["Interview Preps", usage.total_interview_preps || 0],
              ["Career Paths", usage.total_career_paths || 0],
              ["Job Applications", usage.total_job_apps || 0],
              ["Extension Uses", usage.total_extension_uses || 0],
            ].map(([label, count]) => (
              <div key={label} className="flex items-center justify-between">
                <span className="text-gray-400">{label}</span>
                <span className="text-white font-medium">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
