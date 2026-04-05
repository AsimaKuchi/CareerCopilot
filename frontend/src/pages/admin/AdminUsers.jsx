import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Search,
  ChevronLeft,
  ChevronRight,
  Crown,
  Ban,
  Lock,
  Download,
  MoreVertical,
} from "lucide-react";
import { apiFetch } from "../../utils/apiFetch";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL;

export default function AdminUsers() {
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [planFilter, setPlanFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [actionMenu, setActionMenu] = useState(null);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page, limit: 20 });
      if (search) params.set("search", search);
      if (planFilter) params.set("plan", planFilter);
      if (statusFilter) params.set("status", statusFilter);

      const res = await fetch(`${API}/api/admin/users?${params}`, {
        credentials: "include",
      });
      const data = await res.json();
      setUsers(data.users || []);
      setTotal(data.total || 0);
      setPages(data.pages || 1);
    } catch {
      toast.error("Failed to load users");
    } finally {
      setLoading(false);
    }
  }, [page, search, planFilter, statusFilter]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleBan = async (userId) => {
    if (!window.confirm("Are you sure you want to ban this user?")) return;
    try {
      await apiFetch(`${API}/api/admin/users/${userId}/ban`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ reason: "Admin action" }),
      });
      toast.success("User banned");
      fetchUsers();
    } catch {
      toast.error("Failed to ban user");
    }
    setActionMenu(null);
  };

  const handleUnban = async (userId) => {
    try {
      await apiFetch(`${API}/api/admin/users/${userId}/unban`, {
        method: "POST",
        credentials: "include",
      });
      toast.success("User unbanned");
      fetchUsers();
    } catch {
      toast.error("Failed to unban user");
    }
    setActionMenu(null);
  };

  const handleUnlock = async (userId) => {
    try {
      await apiFetch(`${API}/api/admin/users/${userId}/unlock`, {
        method: "POST",
        credentials: "include",
      });
      toast.success("Account unlocked");
      fetchUsers();
    } catch {
      toast.error("Failed to unlock");
    }
    setActionMenu(null);
  };

  const handleExport = async () => {
    try {
      const res = await fetch(`${API}/api/admin/users/export/csv`, {
        credentials: "include",
      });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `users_export.csv`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Export downloaded");
    } catch {
      toast.error("Export failed");
    }
  };

  return (
    <div className="p-8" data-testid="admin-users">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">User Management</h1>
        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-4 py-2 bg-gray-800 text-gray-300 rounded-lg text-sm hover:bg-gray-700 transition-colors"
          data-testid="export-users-btn"
        >
          <Download className="w-4 h-4" />
          Export CSV
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Search by name or email..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full pl-10 pr-4 py-2.5 bg-gray-900 border border-gray-800 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
            data-testid="user-search-input"
          />
        </div>
        <select
          value={planFilter}
          onChange={(e) => {
            setPlanFilter(e.target.value);
            setPage(1);
          }}
          className="px-3 py-2.5 bg-gray-900 border border-gray-800 rounded-lg text-sm text-white focus:outline-none"
          data-testid="plan-filter"
        >
          <option value="">All Plans</option>
          <option value="free">Free</option>
          <option value="pro">Pro</option>
        </select>
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
          className="px-3 py-2.5 bg-gray-900 border border-gray-800 rounded-lg text-sm text-white focus:outline-none"
          data-testid="status-filter"
        >
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="banned">Banned</option>
          <option value="locked">Locked</option>
        </select>
      </div>

      {/* Users Table */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-800">
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">User</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Plan</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Joined</th>
              <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {loading ? (
              <tr>
                <td colSpan={5} className="px-4 py-12 text-center text-gray-500">
                  Loading...
                </td>
              </tr>
            ) : users.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-12 text-center text-gray-500">
                  No users found
                </td>
              </tr>
            ) : (
              users.map((user) => {
                const isPro = user.subscription_status === "active";
                const isBanned = user.banned;
                const isLocked = (user.failed_login_attempts || 0) >= 5;
                return (
                  <tr key={user.user_id} className="hover:bg-gray-800/50 transition-colors">
                    <td className="px-4 py-3">
                      <button
                        onClick={() => navigate(`/admin/users/${user.user_id}`)}
                        className="text-left"
                      >
                        <p className="text-sm font-medium text-white hover:text-indigo-400 transition-colors">
                          {user.name || "No name"}
                        </p>
                        <p className="text-xs text-gray-500">{user.email}</p>
                      </button>
                    </td>
                    <td className="px-4 py-3">
                      {isPro ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-500/20 text-indigo-400">
                          <Crown className="w-3 h-3" /> Pro
                        </span>
                      ) : (
                        <span className="text-xs text-gray-500">Free</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {isBanned ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-500/20 text-red-400">
                          <Ban className="w-3 h-3" /> Banned
                        </span>
                      ) : isLocked ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-500/20 text-amber-400">
                          <Lock className="w-3 h-3" /> Locked
                        </span>
                      ) : (
                        <span className="text-xs text-emerald-400">Active</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500">
                      {user.created_at
                        ? new Date(user.created_at).toLocaleDateString()
                        : "—"}
                    </td>
                    <td className="px-4 py-3 text-right relative">
                      <button
                        onClick={() =>
                          setActionMenu(actionMenu === user.user_id ? null : user.user_id)
                        }
                        className="p-1 text-gray-500 hover:text-gray-300 rounded"
                      >
                        <MoreVertical className="w-4 h-4" />
                      </button>
                      {actionMenu === user.user_id && (
                        <div className="absolute right-4 top-10 z-10 w-44 bg-gray-800 border border-gray-700 rounded-lg shadow-xl py-1">
                          <button
                            onClick={() => navigate(`/admin/users/${user.user_id}`)}
                            className="w-full text-left px-3 py-2 text-sm text-gray-300 hover:bg-gray-700"
                          >
                            View Details
                          </button>
                          {isLocked && (
                            <button
                              onClick={() => handleUnlock(user.user_id)}
                              className="w-full text-left px-3 py-2 text-sm text-amber-400 hover:bg-gray-700"
                            >
                              Unlock Account
                            </button>
                          )}
                          {isBanned ? (
                            <button
                              onClick={() => handleUnban(user.user_id)}
                              className="w-full text-left px-3 py-2 text-sm text-emerald-400 hover:bg-gray-700"
                            >
                              Unban User
                            </button>
                          ) : user.role !== "admin" ? (
                            <button
                              onClick={() => handleBan(user.user_id)}
                              className="w-full text-left px-3 py-2 text-sm text-red-400 hover:bg-gray-700"
                            >
                              Ban User
                            </button>
                          ) : null}
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>

        {/* Pagination */}
        {pages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-800">
            <span className="text-sm text-gray-500">
              {total} users total
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page <= 1}
                className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-800 disabled:opacity-30"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-sm text-gray-400">
                Page {page} of {pages}
              </span>
              <button
                onClick={() => setPage(Math.min(pages, page + 1))}
                disabled={page >= pages}
                className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-800 disabled:opacity-30"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
