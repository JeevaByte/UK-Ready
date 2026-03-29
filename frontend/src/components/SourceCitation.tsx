import clsx from "clsx";
import type { Source } from "@/lib/api";

interface SourceCitationProps {
  confidence: "HIGH" | "MEDIUM" | "LOW";
  sources: Source[];
  disclaimer: string;
}

const CONFIDENCE_CONFIG = {
  HIGH: {
    label: "High confidence",
    description: "Directly stated in gov.uk guidance",
    bgClass: "bg-green-50 border-green-200 text-green-800",
    dotClass: "bg-brand-green",
  },
  MEDIUM: {
    label: "Medium confidence",
    description: "Inferred from gov.uk guidance",
    bgClass: "bg-amber-50 border-amber-200 text-amber-800",
    dotClass: "bg-brand-amber",
  },
  LOW: {
    label: "Low confidence",
    description: "Uncertain — please verify at gov.uk",
    bgClass: "bg-red-50 border-red-200 text-red-800",
    dotClass: "bg-brand-red",
  },
};

/**
 * Displays confidence level, gov.uk source links, and the legal disclaimer
 * below an assistant message.
 *
 * Confidence is shown as a coloured badge (green/amber/red) so users can
 * quickly judge how reliable an answer is. LOW confidence answers get
 * a prominent warning encouraging professional advice.
 */
export default function SourceCitation({
  confidence,
  sources,
  disclaimer,
}: SourceCitationProps) {
  const config = CONFIDENCE_CONFIG[confidence];

  return (
    <div className="mt-3 pt-3 border-t border-gray-200 space-y-2">
      {/* Confidence badge */}
      <div
        className={clsx(
          "inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border",
          config.bgClass
        )}
      >
        <span
          className={clsx("w-2 h-2 rounded-full flex-shrink-0", config.dotClass)}
          aria-hidden="true"
        />
        <span>
          <strong>{config.label}</strong> — {config.description}
        </span>
      </div>

      {/* Source links */}
      {sources.length > 0 && (
        <div>
          <p className="text-xs font-medium text-gray-600 mb-1">Sources:</p>
          <ul className="space-y-1">
            {sources.map((source, index) => (
              <li key={index}>
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-brand-blue hover:underline break-all"
                >
                  {source.title || source.url}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Legal disclaimer — always shown */}
      <p className="text-xs text-gray-500 italic leading-snug">{disclaimer}</p>
    </div>
  );
}
