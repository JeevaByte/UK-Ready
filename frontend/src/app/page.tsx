import VisaSelector from "@/components/VisaSelector";

/**
 * Landing page — the entry point of UKReady.
 *
 * Shows a brief value proposition and the visa type selector.
 * On selection, the user is taken to /chat with their visa type stored
 * in localStorage.
 */
export default function HomePage() {
  return (
    <div className="max-w-3xl mx-auto">
      {/* Hero */}
      <div className="mb-10">
        <h1 className="text-3xl font-bold text-brand-blue-dark mb-3">
          Get clear answers about your UK visa
        </h1>
        <p className="text-lg text-gray-700 leading-relaxed">
          UKReady gives you accurate, sourced answers about your work rights,
          visa rules, and UK migration — specific to{" "}
          <strong>your visa type</strong>. Every answer cites official gov.uk
          guidance.
        </p>
        <p className="mt-3 text-gray-600">
          Select your visa type to get started.
        </p>
      </div>

      {/* Visa selector */}
      <VisaSelector />

      {/* Trust signals */}
      <div className="mt-12 grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm text-gray-600">
        <div className="flex items-start gap-2">
          <span className="text-brand-green font-bold text-base mt-0.5">✓</span>
          <span>Answers sourced from official gov.uk guidance</span>
        </div>
        <div className="flex items-start gap-2">
          <span className="text-brand-green font-bold text-base mt-0.5">✓</span>
          <span>Specific to your visa type — no generic answers</span>
        </div>
        <div className="flex items-start gap-2">
          <span className="text-brand-green font-bold text-base mt-0.5">✓</span>
          <span>Free and open source. No account needed.</span>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="mt-10 p-4 bg-yellow-50 border-l-4 border-yellow-400 text-sm text-yellow-900 rounded">
        <strong>Important:</strong> UKReady provides information, not legal
        advice. For visa decisions, always consult a registered immigration
        solicitor or adviser.
      </div>
    </div>
  );
}
