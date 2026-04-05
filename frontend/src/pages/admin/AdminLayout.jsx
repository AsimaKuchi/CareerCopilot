import { useState, useEffect } from "react";
import { useNavigate, useLocation, Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  Shield,
  FileText,
  Headphones,
  ChevronLeft,
} from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL;

const NAV_ITEMS = [
  { path: "/admin", icon: LayoutDashboard, label: "Overview", exact: true },
  { path: "/admin/users", icon: Users, label: "Users" },
  { path: "/admin/security", icon: Shield, label: "Security" },
  { path: "/admin/audit-logs", icon: FileText, label: "Audit Logs" },
  { path: "/admin/support", icon: Headphones, label: "Support" },
];

export default function AdminLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [admin, setAdmin] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/auth/me`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (!data || data.role !== "admin") {
          navigate("/dashboard");
        } else {
          setAdmin(data);
        }
        setLoading(false);
      })
      .catch(() => {
        navigate("/auth");
        setLoading(false);
      });
  }, [navigate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!admin) return null;

  const isActive = (item) => {
    if (item.exact) return location.pathname === item.path;
    return location.pathname.startsWith(item.path);
  };

  return (
    <div className="min-h-screen bg-gray-950 flex" data-testid="admin-layout">
      {/* Sidebar */}
      <aside className="w-60 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Admin Panel</h2>
              <p className="text-xs text-gray-500">{admin.email}</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = isActive(item);
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  active
                    ? "bg-indigo-600/20 text-indigo-400"
                    : "text-gray-400 hover:text-gray-200 hover:bg-gray-800"
                }`}
                data-testid={`admin-nav-${item.label.toLowerCase().replace(" ", "-")}`}
              >
                <Icon className="w-4 h-4" />
                {item.label}
              </button>
            );
          })}
        </nav>

        <div className="p-3 border-t border-gray-800 space-y-1">
          <button
            onClick={() => navigate("/dashboard")}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-400 hover:text-gray-200 hover:bg-gray-800 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            Back to App
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Outlet context={{ admin }} />
      </main>
    </div>
  );
}
