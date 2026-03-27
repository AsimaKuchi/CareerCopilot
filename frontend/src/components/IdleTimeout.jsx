import { useEffect, useRef, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { API } from "@/App";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogAction,
} from "@/components/ui/alert-dialog";
import { Clock, LogOut } from "lucide-react";

const IDLE_LIMIT = 60 * 60 * 1000;   // 60 minutes
const WARN_BEFORE = 5 * 60 * 1000;   // warn 5 min before
const WARN_AT = IDLE_LIMIT - WARN_BEFORE; // 55 min
const TICK = 1000;

const EVENTS = ["mousedown", "keydown", "scroll", "touchstart", "mousemove"];

export default function IdleTimeout() {
  const navigate = useNavigate();
  const [showWarning, setShowWarning] = useState(false);
  const [countdown, setCountdown] = useState(WARN_BEFORE / 1000);
  const lastActivity = useRef(Date.now());
  const warnTimer = useRef(null);
  const logoutTimer = useRef(null);
  const tickInterval = useRef(null);

  const logout = useCallback(async () => {
    clearAll();
    try {
      await fetch(`${API}/auth/logout`, { method: "POST", credentials: "include" });
    } catch {}
    navigate("/auth", { replace: true });
  }, [navigate]);

  const clearAll = () => {
    clearTimeout(warnTimer.current);
    clearTimeout(logoutTimer.current);
    clearInterval(tickInterval.current);
  };

  const resetTimers = useCallback(() => {
    lastActivity.current = Date.now();
    setShowWarning(false);
    clearAll();

    warnTimer.current = setTimeout(() => {
      setShowWarning(true);
      setCountdown(WARN_BEFORE / 1000);
      tickInterval.current = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(tickInterval.current);
            return 0;
          }
          return prev - 1;
        });
      }, TICK);
    }, WARN_AT);

    logoutTimer.current = setTimeout(() => {
      logout();
    }, IDLE_LIMIT);
  }, [logout]);

  const stayLoggedIn = () => {
    resetTimers();
  };

  useEffect(() => {
    const onActivity = () => {
      if (!showWarning) resetTimers();
    };

    EVENTS.forEach((e) => window.addEventListener(e, onActivity, { passive: true }));
    resetTimers();

    return () => {
      EVENTS.forEach((e) => window.removeEventListener(e, onActivity));
      clearAll();
    };
  }, [resetTimers, showWarning]);

  const minutes = Math.floor(countdown / 60);
  const seconds = countdown % 60;

  return (
    <AlertDialog open={showWarning} onOpenChange={() => {}}>
      <AlertDialogContent className="max-w-sm bg-white border border-gray-200 shadow-xl" data-testid="idle-timeout-dialog">
        <AlertDialogHeader>
          <div className="w-12 h-12 rounded-full bg-amber-50 flex items-center justify-center mx-auto mb-2">
            <Clock className="w-6 h-6 text-amber-500" />
          </div>
          <AlertDialogTitle className="text-center text-gray-900">
            Session Expiring Soon
          </AlertDialogTitle>
          <AlertDialogDescription className="text-center text-gray-500">
            You've been inactive for a while. For your security, you'll be logged out in{" "}
            <span className="font-semibold text-amber-600 tabular-nums">
              {minutes}:{seconds.toString().padStart(2, "0")}
            </span>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter className="flex-col gap-2 sm:flex-col">
          <AlertDialogAction
            data-testid="stay-logged-in-btn"
            onClick={stayLoggedIn}
            className="w-full bg-indigo-500 hover:bg-indigo-600 text-white"
          >
            Stay Logged In
          </AlertDialogAction>
          <button
            data-testid="logout-now-btn"
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 text-sm text-gray-500 hover:text-gray-700 py-2 transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            Log out now
          </button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
