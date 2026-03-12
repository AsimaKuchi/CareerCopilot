import { useNavigate, useLocation } from "react-router-dom";
import { API } from "@/App";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  LayoutDashboard,
  Search,
  User,
  FileText,
  MessageSquare,
  LogOut,
  Menu,
  X,
  Home,
  HelpCircle,
  Compass,
} from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

export const Navbar = ({ user }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = async () => {
    try {
      await fetch(`${API}/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
      navigate("/", { replace: true });
      toast.success("Logged out successfully");
    } catch (error) {
      navigate("/", { replace: true });
    }
  };

  const navItems = [
    { icon: LayoutDashboard, label: "Dashboard", path: "/dashboard" },
    { icon: Search, label: "Find Jobs", path: "/jobs" },
    { icon: FileText, label: "Applications", path: "/applications" },
    { icon: MessageSquare, label: "Interview Prep", path: "/interview-prep" },
    { icon: Compass, label: "Career Paths", path: "/career-paths" },
    { icon: User, label: "Profile", path: "/profile" },
    { icon: HelpCircle, label: "Support", path: "/support" },
    { icon: Home, label: "Home", path: "/" },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="sticky top-0 z-50 bg-white border-b border-gray-200" data-testid="navbar">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex items-center justify-between h-14">
          {/* Logo */}
          <div
            className="flex items-center gap-1 cursor-pointer group"
            onClick={() => navigate("/dashboard")}
          >
            <div className="relative leading-tight">
              <div className="flex items-center">
                <span className="text-base font-bold text-gray-900 tracking-tight">MyCareer</span>
                <svg className="w-3 h-3 text-gray-400 ml-0.5 -mt-0.5 -rotate-45" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M21 16v-2l-8-5V3.5A1.5 1.5 0 0 0 11.5 2A1.5 1.5 0 0 0 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z" />
                </svg>
              </div>
              <div className="flex items-center -mt-1">
                <svg className="w-2.5 h-3 text-indigo-400 -mr-0.5 flex-shrink-0" viewBox="0 0 12 20" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M11 1C6 1 2 4 2 8C2 12 6 14 6 14" />
                </svg>
                <span className="text-base font-bold text-indigo-500 tracking-tight">CoPilot</span>
              </div>
            </div>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-0.5">
            {navItems.map((item) => (
              <button
                key={item.path}
                data-testid={`nav-${item.label.toLowerCase().replace(/\s/g, '-')}`}
                onClick={() => navigate(item.path)}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-200 ${
                  isActive(item.path)
                    ? "bg-indigo-50 text-indigo-600"
                    : "text-gray-500 hover:text-gray-900 hover:bg-gray-50"
                }`}
              >
                <item.icon className="w-3.5 h-3.5" />
                {item.label}
              </button>
            ))}
          </div>

          {/* User Menu */}
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden h-8 w-8"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </Button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="flex items-center gap-2 p-1 rounded-lg hover:bg-gray-50 transition-colors duration-200" data-testid="user-menu-trigger">
                  <Avatar className="h-7 w-7">
                    <AvatarImage src={user?.picture} alt={user?.name} />
                    <AvatarFallback className="bg-indigo-500 text-white text-xs font-medium">
                      {user?.name?.charAt(0) || "U"}
                    </AvatarFallback>
                  </Avatar>
                  <span className="text-sm font-medium text-gray-700 hidden sm:block max-w-[100px] truncate">
                    {user?.name?.split(" ")[0]}
                  </span>
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56 bg-white border-gray-200 shadow-lg">
                <div className="px-3 py-2">
                  <p className="text-sm font-medium text-gray-900">{user?.name}</p>
                  <p className="text-xs text-gray-500 truncate">{user?.email}</p>
                </div>
                <DropdownMenuSeparator className="bg-gray-100" />
                <DropdownMenuItem onClick={() => navigate("/profile")} className="cursor-pointer text-gray-700 focus:bg-gray-50">
                  <User className="w-4 h-4 mr-2" />
                  Profile Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-gray-100" />
                <DropdownMenuItem data-testid="logout-btn" onClick={handleLogout} className="cursor-pointer text-red-600 focus:text-red-600 focus:bg-red-50">
                  <LogOut className="w-4 h-4 mr-2" />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden py-3 border-t border-gray-100">
            <div className="flex flex-col gap-0.5">
              {navItems.map((item) => (
                <button
                  key={item.path}
                  onClick={() => { navigate(item.path); setMobileMenuOpen(false); }}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
                    isActive(item.path)
                      ? "bg-indigo-50 text-indigo-600"
                      : "text-gray-500 hover:text-gray-900 hover:bg-gray-50"
                  }`}
                >
                  <item.icon className="w-4 h-4" />
                  {item.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
