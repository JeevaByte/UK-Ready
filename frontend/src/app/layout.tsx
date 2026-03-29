import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "UKReady — AI navigator for UK skilled migrants",
  description:
    "Get visa-aware answers about your UK work rights, visa rules, and migration questions. " +
    "Sourced from official gov.uk guidance. Free and open source.",
  keywords: [
    "UK visa",
    "skilled migrants",
    "graduate visa",
    "skilled worker visa",
    "UK immigration",
    "work rights UK",
    "ILR",
  ],
  openGraph: {
    title: "UKReady — AI navigator for UK skilled migrants",
    description:
      "Get visa-aware answers about your UK work rights. Sourced from gov.uk.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-white font-sans text-gray-900 antialiased">
        {/* Skip to main content for accessibility */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:bg-brand-blue focus:text-white focus:px-4 focus:py-2"
        >
          Skip to main content
        </a>

        {/* Header */}
        <header className="bg-brand-blue-dark border-b-4 border-brand-blue">
          <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
            <a
              href="/"
              className="text-white font-bold text-xl tracking-tight hover:underline"
            >
              UKReady
            </a>
            <span className="text-blue-200 text-sm hidden sm:block">
              AI navigator for UK skilled migrants
            </span>
          </div>
        </header>

        {/* Main content */}
        <main id="main-content" className="max-w-5xl mx-auto px-4 py-8">
          {children}
        </main>

        {/* Footer */}
        <footer className="mt-16 border-t border-gray-200 py-8 text-center text-sm text-gray-500">
          <p>
            UKReady is free, open source, and not affiliated with the UK government.
          </p>
          <p className="mt-1">
            Always verify visa rules at{" "}
            <a
              href="https://www.gov.uk"
              target="_blank"
              rel="noopener noreferrer"
              className="text-brand-blue hover:underline"
            >
              gov.uk
            </a>
            {" "}and consult a registered immigration solicitor for legal advice.
          </p>
          <p className="mt-2">
            <a
              href="https://github.com/jeevabyte/uk-ready"
              target="_blank"
              rel="noopener noreferrer"
              className="text-brand-blue hover:underline"
            >
              View on GitHub
            </a>
            {" · "}
            <a
              href="https://github.com/jeevabyte/uk-ready/blob/main/LICENSE"
              target="_blank"
              rel="noopener noreferrer"
              className="text-brand-blue hover:underline"
            >
              MIT License
            </a>
          </p>
        </footer>
      </body>
    </html>
  );
}
