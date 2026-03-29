"use client";

import { useRouter } from "next/navigation";
import clsx from "clsx";
import { useVisaContext } from "@/hooks/useVisaContext";
import { VISA_DESCRIPTIONS, VISA_DISPLAY_NAMES, type VisaType } from "@/lib/api";

const VISA_TYPES: VisaType[] = ["GRADUATE", "SKILLED_WORKER", "STUDENT", "ILR"];

const VISA_ICONS: Record<VisaType, string> = {
  GRADUATE: "🎓",
  SKILLED_WORKER: "💼",
  STUDENT: "📚",
  ILR: "🏠",
};

/**
 * Visa type selector component.
 *
 * Displays a grid of 4 visa type cards. On click, saves the selection
 * to localStorage and navigates to the /chat page.
 *
 * Designed to be accessible: each card is a button with clear focus
 * states, and the selected state is visually distinct.
 */
export default function VisaSelector() {
  const router = useRouter();
  const { visaType, setVisaType } = useVisaContext();

  const handleSelect = (selected: VisaType) => {
    setVisaType(selected);
    router.push("/chat");
  };

  return (
    <div>
      <h2 className="text-lg font-semibold text-gray-800 mb-4">
        Which visa are you on?
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {VISA_TYPES.map((type) => (
          <button
            key={type}
            onClick={() => handleSelect(type)}
            className={clsx(
              "text-left p-5 rounded-lg border-2 transition-all duration-150",
              "focus:outline-none focus:ring-4 focus:ring-brand-blue focus:ring-opacity-30",
              "hover:border-brand-blue hover:bg-blue-50",
              visaType === type
                ? "border-brand-blue bg-blue-50"
                : "border-gray-200 bg-white"
            )}
            aria-pressed={visaType === type}
          >
            <div className="flex items-start gap-3">
              <span className="text-2xl" aria-hidden="true">
                {VISA_ICONS[type]}
              </span>
              <div>
                <div className="font-semibold text-gray-900 mb-1">
                  {VISA_DISPLAY_NAMES[type]}
                </div>
                <div className="text-sm text-gray-600 leading-snug">
                  {VISA_DESCRIPTIONS[type]}
                </div>
              </div>
            </div>
            {visaType === type && (
              <div className="mt-3 text-xs font-medium text-brand-blue">
                ✓ Currently selected — click to start chatting
              </div>
            )}
          </button>
        ))}
      </div>

      <p className="mt-4 text-xs text-gray-500">
        Your visa selection is stored locally in your browser. We don&apos;t
        collect or store any personal data.
      </p>
    </div>
  );
}
