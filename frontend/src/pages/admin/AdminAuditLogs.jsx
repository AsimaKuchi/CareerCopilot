import { useState, useEffect, useCallback } from "react";
import {
  FileText,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Filter,
} from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL;

const TYPE_COLORS = {
  admin_action: "bg-indigo-500/20 text-indigo-400",
  failed_login: "bg-red-500/20 text-red-400",
  login_success: "bg-emerald-500/20 text-emerald-400",
  signup: "bg-blue-500/20 text-blue-400",
  subscription: "bg-amber-500/20 text-amber-400",
};

export default function AdminAuditLogs() {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [page, setPage] = useState(1);
  const [logType, setLogType] = useState("");
  const [logTypes, setLogTypes] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page, limit: 50 });
      if (logType) params.set("log_type", logType);

      const res = await fetch(`${API}/api/admin/audit-logs?${params}`, {
        credentials: "include",
      });
      const data = await res.json();
      setLogs(data.logs || []);
      setTotal(data.total || 0);
      setPages(data.pages || 1);
    } catch {
      console.error("Failed to load audit logs");
    } finally {
      setLoading(false);
    }
  }, [page, logType]);

  const fetchTypes = async () => {
    try {
      const res = await fetch(`${API}/api/admin/audit-logs/types`, {
        credentials: "include",
      });
      const data = await res.json();
      setLogTypes(data.types || []);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    fetchTypes();
  }, []);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  return (
    <div className="p-8" data-testid="admin-audit-logs">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Audit Logs</h1>
        <button
          onClick={fetchLogs}
          className="flex items-center gap-2 px-3 py-2 bg-gray-800 text-gray-300 rounded-lg text-sm hover:bg-gray-700"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-6">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <select
            value={logType}
            onChange={(e) => {
              setLogType(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 bg-gray-900 border border-gray-800 rounded-lg text-sm text-white focus:outline-none"
            data-testid="log-type-filter"
          >
            <option value="">All Types</option>
            {logTypes.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
        <span className="text-sm text-gray-500 flex items-center">
          {total} log entries
        </span>
      </div>

      {/* Logs List */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-gray-500">Loading...</div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            <FileText className="w-8 h-8 mx-auto mb-3 opacity-50" />
            <p>No audit logs found</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-800">
            {logs.map((log, i) => {
              const colorClass =
                TYPE_COLORS[log.type] || "bg-gray-700 text-gray-400";
              return (
                <div
                  key={i}
                  className="flex items-start gap-4 px-4 py-3 hover:bg-gray-800/50 transition-colors"
                >
                  <div className="shrink-0 mt-0.5">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${colorClass}`}
                    >
                      {log.type}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      {log.admin_email && (
                        <span className="text-xs text-indigo-400">
                          {log.admin_email}
                        </span>
                      )}
                      {log.action && (
                        <span className="text-sm text-gray-300">
                          {log.action}
                        </span>
                      )}
                      {log.target && (
                        <span className="text-xs text-gray-500">
                          &rarr; {log.target}
                        </span>
                      )}
                    </div>
                    {log.user_email && !log.admin_email && (
                      <p className="text-xs text-gray-500">{log.user_email}</p>
                    )}
                    {log.details && (
                      <p className="text-xs text-gray-500 mt-0.5">
                        {log.details}
                      </p>
                    )}
                  </div>
                  <div className="shrink-0 text-right">
                    <p className="text-xs text-gray-500">
                      {log.timestamp
                        ? new Date(log.timestamp).toLocaleString()
                        : ""}
                    </p>
                    {log.severity && log.severity !== "info" && (
                      <span
                        className={`text-xs ${
                          log.severity === "warning"
                            ? "text-amber-400"
                            : log.severity === "error"
                            ? "text-red-400"
                            : "text-gray-500"
                        }`}
                      >
                        {log.severity}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Pagination */}
        {pages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-800">
            <span className="text-sm text-gray-500">{total} entries</span>
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
