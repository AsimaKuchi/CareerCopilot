import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Crown, X } from "lucide-react";

const FEATURE_NAMES = {
  job_applications: "job applications",
  resume_optimizations: "resume optimizations",
  interview_prep: "interview prep sessions",
  career_paths: "career path analyses",
  cover_letters: "cover letter generations",
  extension_uses: "extension uses",
};

export function UpgradeModal({ feature, current, limit, onClose }) {
  const navigate = useNavigate();
  const featureName = FEATURE_NAMES[feature] || feature;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" data-testid="upgrade-modal">
      <div className="bg-white rounded-2xl shadow-xl max-w-md w-full mx-4 p-6 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
          data-testid="upgrade-modal-close"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-xl bg-amber-100 flex items-center justify-center">
            <Crown className="w-6 h-6 text-amber-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Monthly Limit Reached
            </h3>
            <p className="text-sm text-gray-500">
              {current}/{limit} {featureName} used
            </p>
          </div>
        </div>

        <p className="text-gray-600 mb-6">
          You've used all your free {featureName} this month.
          Upgrade to <span className="font-semibold text-indigo-600">Pro</span>{" "}
          for unlimited access to every feature.
        </p>

        <div className="bg-indigo-50 rounded-xl p-4 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-semibold text-gray-900">Pro Plan</p>
              <p className="text-sm text-gray-500">Unlimited everything</p>
            </div>
            <p className="text-xl font-bold text-gray-900">
              $19.99<span className="text-sm font-normal text-gray-500">/mo</span>
            </p>
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 rounded-xl border border-gray-300 text-gray-700 font-medium hover:bg-gray-50 transition-colors"
          >
            Maybe Later
          </button>
          <button
            onClick={() => {
              onClose();
              navigate("/pricing");
            }}
            className="flex-1 py-2.5 rounded-xl bg-indigo-600 text-white font-medium hover:bg-indigo-700 transition-colors flex items-center justify-center gap-2"
            data-testid="upgrade-modal-cta"
          >
            <Crown className="w-4 h-4" />
            Upgrade Now
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Hook to handle 402 usage limit errors from API responses.
 * Returns [upgradeInfo, setUpgradeInfo, handleApiError] where:
 * - upgradeInfo: null or { feature, current, limit } to show UpgradeModal
 * - handleApiError: function to call with a fetch Response when status is 402
 */
export function useUpgradeModal() {
  const [upgradeInfo, setUpgradeInfo] = useState(null);

  const handleApiError = async (response) => {
    if (response.status === 402) {
      try {
        const data = await response.json();
        const detail = data.detail || data;
        if (detail.error === "usage_limit_reached") {
          setUpgradeInfo({
            feature: detail.feature,
            current: detail.current,
            limit: detail.limit,
          });
          return true;
        }
      } catch {
        // Not a usage limit error
      }
    }
    return false;
  };

  return { upgradeInfo, setUpgradeInfo, handleApiError };
}
