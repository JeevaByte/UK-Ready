"use client";

import { useCallback, useEffect, useState } from "react";
import type { VisaType } from "@/lib/api";

const STORAGE_KEY = "ukready_visa_type";

/**
 * Custom hook for managing the user's visa type selection.
 *
 * Persists the visa type to localStorage so the user doesn't need to
 * reselect on every page load or browser refresh.
 *
 * Returns:
 * - visaType: The currently selected visa type, or null if not set
 * - setVisaType: Function to update and persist the visa type
 * - clearVisaType: Function to clear the selection (back to landing page)
 */
export function useVisaContext() {
  const [visaType, setVisaTypeState] = useState<VisaType | null>(null);

  // Load from localStorage on mount (client-side only)
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        setVisaTypeState(stored as VisaType);
      }
    } catch {
      // localStorage may be unavailable in some browsers/contexts
    }
  }, []);

  const setVisaType = useCallback((visa: VisaType) => {
    setVisaTypeState(visa);
    try {
      localStorage.setItem(STORAGE_KEY, visa);
    } catch {
      // Silently fail if localStorage is unavailable
    }
  }, []);

  const clearVisaType = useCallback(() => {
    setVisaTypeState(null);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // Silently fail if localStorage is unavailable
    }
  }, []);

  return { visaType, setVisaType, clearVisaType };
}
