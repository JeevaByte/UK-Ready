"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import ChatInterface from "@/components/ChatInterface";
import { useVisaContext } from "@/hooks/useVisaContext";
import { VISA_DISPLAY_NAMES, type VisaType } from "@/lib/api";

/**
 * Chat page — the core Q&A interface.
 *
 * Reads the user's visa type from localStorage. If no visa type is set,
 * redirects to the landing page to select one first.
 *
 * Renders the visa type badge at the top (with a "change visa" link)
 * and the full ChatInterface below.
 */
export default function ChatPage() {
  const router = useRouter();
  const { visaType, clearVisaType } = useVisaContext();
  const [mounted, setMounted] = useState(false);

  // Wait for client-side hydration before checking localStorage
  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !visaType) {
      router.push("/");
    }
  }, [mounted, visaType, router]);

  // Prevent flash of wrong content during hydration
  if (!mounted || !visaType) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  const displayName = VISA_DISPLAY_NAMES[visaType as VisaType];

  const handleChangeVisa = () => {
    clearVisaType();
    router.push("/");
  };

  return (
    <div className="max-w-3xl mx-auto">
      {/* Visa context banner */}
      <div className="flex items-center justify-between mb-6 p-3 bg-brand-grey-light rounded-lg border border-gray-200">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Answering for:</span>
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-brand-blue text-white">
            {displayName}
          </span>
        </div>
        <button
          onClick={handleChangeVisa}
          className="text-sm text-brand-blue hover:underline focus:outline-none focus:ring-2 focus:ring-brand-blue rounded"
        >
          Change visa
        </button>
      </div>

      {/* Chat interface */}
      <ChatInterface visaType={visaType as VisaType} />

      {/* Help text */}
      <div className="mt-4 text-sm text-gray-500 text-center">
        <p>
          Try asking:{" "}
          <em>&ldquo;Can I switch employers?&rdquo;</em>{" "}
          or{" "}
          <em>&ldquo;What are my work hour limits?&rdquo;</em>
        </p>
      </div>
    </div>
  );
}
