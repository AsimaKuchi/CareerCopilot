import { useState, useEffect, useCallback } from "react";
import {
  Monitor,
  Smartphone,
  Globe,
  LogOut,
  Shield,
  Loader2,
} from "lucide-react";
import { apiFetch } from "../utils/apiFetch";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL;

function parseUserAgent(ua) {
  if (!ua || ua === "Unknown") return { device: "Unknown", browser: "Unknown" };
  
  let browser = "Unknown";
  let device = "Desktop";

  if (ua.includes("Mobile") || ua.includes("Android")) device = "Mobile";
  else if (ua.includes("Tablet") || ua.includes("iPad")) device = "Tablet";

  if (ua.includes("Chrome") && !ua.includes("Edg")) browser = "Chrome";
  else if (ua.includes("Firefox")) browser = "Firefox";
  else if (ua.includes("Safari") && !ua.includes("Chrome")) browser = "Safari";
  else if (ua.includes("Edg")) browser = "Edge";
  else if (ua.includes("curl")) browser = "API Client";

  return { device, browser };
}

export default function SessionManagement() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [revoking, setRevoking] = useState(false);

  const fetchSessions = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/auth/sessions`, {
        credentials: "include",
      });
      const data = await res.json();
      setSessions(data.sessions || []);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const handleRevokeAll = async () => {
    if (!window.confirm("This will log you out from all other devices. Continue?"))
      return;
    setRevoking(true);
    try {
      const res = await apiFetch(`${API}/api/auth/revoke-all-sessions`, {
        method: "POST",
        credentials: "include",
      });
      const data = await res.json();
      toast.success(data.message);
      fetchSessions();
    } catch {
      toast.error("Failed to revoke sessions");
    } finally {
      setRevoking(false);
    }
  };

  const otherSessions = sessions.filter((s) => !s.is_current);

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden" data-testid="session-management">
      <div className="p-5 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-50 flex items-center justify-center">
            <Shield className="w-4 h-4 text-indigo-600" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-gray-900">Active Sessions</h3>
            <p className="text-sm text-gray-500">{sessions.length} active session(s)</p>
          </div>
        </div>
        {otherSessions.length > 0 && (
          <button
            onClick={handleRevokeAll}
            disabled={revoking}
            className="flex items-center gap-2 px-3 py-2 text-sm rounded-lg border border-red-200 text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50"
            data-testid="revoke-all-sessions-btn"
          >
            <LogOut className="w-3.5 h-3.5" />
            {revoking ? "Revoking..." : "Logout All Devices"}
          </button>
        )}
      </div>

      {loading ? (
        <div className="p-8 flex items-center justify-center">
          <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
        </div>
      ) : sessions.length === 0 ? (
        <div className="p-8 text-center text-gray-500 text-sm">
          No active sessions found
        </div>
      ) : (
        <div className="divide-y divide-gray-100">
          {sessions.map((session, i) => {
            const { device, browser } = parseUserAgent(session.user_agent);
            const DeviceIcon = device === "Mobile" ? Smartphone : Monitor;

            return (
              <div
                key={i}
                className={`flex items-center gap-4 px-5 py-4 ${
                  session.is_current ? "bg-indigo-50/50" : ""
                }`}
              >
                <div className="w-9 h-9 rounded-lg bg-gray-100 flex items-center justify-center shrink-0">
                  <DeviceIcon className="w-4 h-4 text-gray-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-gray-900">
                      {browser} on {device}
                    </p>
                    {session.is_current && (
                      <span className="px-1.5 py-0.5 text-xs rounded bg-indigo-100 text-indigo-700 font-medium">
                        This device
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 mt-0.5">
                    <span className="text-xs text-gray-500 flex items-center gap-1">
                      <Globe className="w-3 h-3" />
                      {session.ip_address || "Unknown IP"}
                    </span>
                    <span className="text-xs text-gray-400">
                      Last active:{" "}
                      {session.last_active
                        ? new Date(session.last_active).toLocaleString()
                        : "Unknown"}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
