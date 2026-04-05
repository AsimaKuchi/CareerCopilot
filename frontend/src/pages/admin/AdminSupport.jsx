import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Search,
  Crown,
  Ban,
  Lock,
  Send,
  User,
} from "lucide-react";
import { apiFetch } from "../../utils/apiFetch";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL;

export default function AdminSupport() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [notifUserId, setNotifUserId] = useState(null);
  const [notifMessage, setNotifMessage] = useState("");
  const [sending, setSending] = useState(false);

  const handleSearch = async () => {
    if (query.length < 2) return;
    setSearching(true);
    try {
      const res = await fetch(
        `${API}/api/admin/support/search?q=${encodeURIComponent(query)}`,
        { credentials: "include" }
      );
      const data = await res.json();
      setResults(data.users || []);
    } catch {
      toast.error("Search failed");
    } finally {
      setSearching(false);
    }
  };

  const handleSendNotification = async () => {
    if (!notifMessage.trim()) return;
    setSending(true);
    try {
      await apiFetch(`${API}/api/admin/support/send-notification`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          user_id: notifUserId,
          message: notifMessage,
          type: "info",
        }),
      });
      toast.success("Notification sent");
      setNotifMessage("");
      setNotifUserId(null);
    } catch {
      toast.error("Failed to send");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="p-8" data-testid="admin-support">
      <h1 className="text-2xl font-bold text-white mb-6">Support Tools</h1>

      {/* User Search */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 mb-6">
        <h3 className="text-lg font-semibold text-white mb-4">Find User</h3>
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              type="text"
              placeholder="Search by email or name..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="w-full pl-10 pr-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
              data-testid="support-search-input"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={searching || query.length < 2}
            className="px-4 py-2.5 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50"
            data-testid="support-search-btn"
          >
            {searching ? "Searching..." : "Search"}
          </button>
        </div>

        {/* Results */}
        {results.length > 0 && (
          <div className="mt-4 space-y-2">
            {results.map((user) => {
              const isPro = user.subscription_status === "active";
              const isBanned = user.banned;
              return (
                <div
                  key={user.user_id}
                  className="flex items-center justify-between px-4 py-3 bg-gray-800 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center">
                      <User className="w-4 h-4 text-gray-400" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white flex items-center gap-2">
                        {user.name || "No name"}
                        {isPro && <Crown className="w-3 h-3 text-indigo-400" />}
                        {isBanned && <Ban className="w-3 h-3 text-red-400" />}
                      </p>
                      <p className="text-xs text-gray-500">{user.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() =>
                        setNotifUserId(
                          notifUserId === user.user_id ? null : user.user_id
                        )
                      }
                      className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-700"
                      title="Send notification"
                    >
                      <Send className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() =>
                        navigate(`/admin/users/${user.user_id}`)
                      }
                      className="px-3 py-1.5 text-xs rounded-lg bg-gray-700 text-gray-300 hover:bg-gray-600"
                    >
                      View Details
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Send Notification Panel */}
      {notifUserId && (
        <div className="bg-gray-900 rounded-xl border border-indigo-800 p-6 mb-6" data-testid="notification-panel">
          <h3 className="text-lg font-semibold text-white mb-4">
            Send Notification
          </h3>
          <p className="text-sm text-gray-400 mb-3">
            To: {results.find((u) => u.user_id === notifUserId)?.email}
          </p>
          <textarea
            value={notifMessage}
            onChange={(e) => setNotifMessage(e.target.value)}
            placeholder="Type your message..."
            rows={3}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 resize-none"
            data-testid="notification-textarea"
          />
          <div className="flex justify-end gap-3 mt-3">
            <button
              onClick={() => {
                setNotifUserId(null);
                setNotifMessage("");
              }}
              className="px-4 py-2 text-sm text-gray-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              onClick={handleSendNotification}
              disabled={sending || !notifMessage.trim()}
              className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
              data-testid="send-notification-btn"
            >
              <Send className="w-3.5 h-3.5" />
              {sending ? "Sending..." : "Send"}
            </button>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
        <div className="grid sm:grid-cols-2 gap-3">
          <button
            onClick={() => navigate("/admin/users")}
            className="flex items-center gap-3 p-4 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors text-left"
          >
            <User className="w-5 h-5 text-indigo-400" />
            <div>
              <p className="text-sm font-medium text-white">Manage Users</p>
              <p className="text-xs text-gray-500">View, ban, unlock accounts</p>
            </div>
          </button>
          <button
            onClick={() => navigate("/admin/security")}
            className="flex items-center gap-3 p-4 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors text-left"
          >
            <Lock className="w-5 h-5 text-amber-400" />
            <div>
              <p className="text-sm font-medium text-white">Security Monitor</p>
              <p className="text-xs text-gray-500">Failed logins, lockouts</p>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}
