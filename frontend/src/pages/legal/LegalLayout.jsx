import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

/**
 * Shared layout for legal pages (Privacy, Terms, Refund).
 * Plain, readable, no marketing chrome — these are documents people skim
 * before signing up or before Stripe/Chrome reviewers approve the app.
 */
export default function LegalLayout({ title, lastUpdated, children }) {
  return (
    <div className="min-h-screen bg-white text-gray-800">
      <header className="border-b border-gray-200">
        <div className="max-w-3xl mx-auto px-6 py-5 flex items-center justify-between">
          <Link
            to="/"
            className="flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-indigo-600 transition-colors"
            data-testid="legal-back-home"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to MyCareerCopilot
          </Link>
          <div className="flex gap-4 text-xs text-gray-500">
            <Link to="/privacy" className="hover:text-indigo-600">Privacy</Link>
            <Link to="/terms" className="hover:text-indigo-600">Terms</Link>
            <Link to="/refunds" className="hover:text-indigo-600">Refunds</Link>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-12">
        <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 tracking-tight mb-2">
          {title}
        </h1>
        <p className="text-sm text-gray-500 mb-10">Last updated: {lastUpdated}</p>
        <article className="prose prose-sm sm:prose prose-gray max-w-none [&_h2]:mt-10 [&_h2]:mb-3 [&_h2]:text-xl [&_h2]:font-semibold [&_h2]:text-gray-900 [&_h3]:mt-6 [&_h3]:mb-2 [&_h3]:text-base [&_h3]:font-semibold [&_p]:my-3 [&_p]:leading-relaxed [&_p]:text-gray-700 [&_ul]:my-3 [&_ul]:pl-6 [&_ul]:list-disc [&_li]:my-1 [&_li]:text-gray-700 [&_strong]:text-gray-900 [&_a]:text-indigo-600 [&_a]:underline hover:[&_a]:text-indigo-700">
          {children}
        </article>
      </main>

      <footer className="border-t border-gray-200 mt-16">
        <div className="max-w-3xl mx-auto px-6 py-8 text-xs text-gray-500 flex flex-wrap items-center justify-between gap-3">
          <span>© {new Date().getFullYear()} MyCareerCopilot. All rights reserved.</span>
          <span>
            Questions? Email{" "}
            <a href="mailto:support@mycareercopilot.ca" className="text-indigo-600 underline">
              support@mycareercopilot.ca
            </a>
          </span>
        </div>
      </footer>
    </div>
  );
}
