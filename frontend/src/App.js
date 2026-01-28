import { useEffect, useRef, useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useLocation, useNavigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import LandingPage from "@/pages/LandingPage";
import HowItWorks from "@/pages/HowItWorks";
import Dashboard from "@/pages/Dashboard";
import Profile from "@/pages/Profile";
import JobSearch from "@/pages/JobSearch";
import Applications from "@/pages/Applications";
import InterviewPrep from "@/pages/InterviewPrep";
import Support from "@/pages/Support";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
const AuthCallback = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const hasProcessed = useRef(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processAuth = async () => {
      const hash = location.hash;
      const sessionId = new URLSearchParams(hash.replace("#", "?")).get("session_id");

      if (!sessionId) {
        navigate("/", { replace: true });
        return;
      }

      try {
        const response = await fetch(`${API}/auth/session`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ session_id: sessionId }),
        });

        if (!response.ok) throw new Error("Auth failed");

        const user = await response.json();
        navigate("/dashboard", { replace: true, state: { user } });
      } catch (error) {
        console.error("Auth error:", error);
        navigate("/", { replace: true });
      }
    };

    processAuth();
  }, [location, navigate]);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-muted-foreground">Signing you in...</p>
      </div>
    </div>
  );
};

const ProtectedRoute = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(null);
  const [user, setUser] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (location.state?.user) {
      setUser(location.state.user);
      setIsAuthenticated(true);
      return;
    }

    const checkAuth = async () => {
      try {
        const response = await fetch(`${API}/auth/me`, {
          credentials: "include",
        });

        if (!response.ok) throw new Error("Not authenticated");

        const userData = await response.json();
        setUser(userData);
        setIsAuthenticated(true);
      } catch (error) {
        setIsAuthenticated(false);
        navigate("/", { replace: true });
      }
    };

    checkAuth();
  }, [navigate, location.state]);

  if (isAuthenticated === null) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return children({ user });
};

const AppRouter = () => {
  const location = useLocation();

  // Check for session_id in URL fragment synchronously
  if (location.hash?.includes("session_id=")) {
    return <AuthCallback />;
  }

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/how-it-works" element={<HowItWorks />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            {({ user }) => <Dashboard user={user} />}
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            {({ user }) => <Profile user={user} />}
          </ProtectedRoute>
        }
      />
      <Route
        path="/jobs"
        element={
          <ProtectedRoute>
            {({ user }) => <JobSearch user={user} />}
          </ProtectedRoute>
        }
      />
      <Route
        path="/applications"
        element={
          <ProtectedRoute>
            {({ user }) => <Applications user={user} />}
          </ProtectedRoute>
        }
      />
      <Route
        path="/interview-prep"
        element={
          <ProtectedRoute>
            {({ user }) => <InterviewPrep user={user} />}
          </ProtectedRoute>
        }
      />
    </Routes>
  );
};

function App() {
  return (
    <div className="min-h-screen bg-background">
      <BrowserRouter>
        <AppRouter />
        <Toaster position="top-right" richColors />
      </BrowserRouter>
    </div>
  );
}

export default App;
