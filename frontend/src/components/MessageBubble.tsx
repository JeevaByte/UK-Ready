import SourceCitation from "./SourceCitation";
import type { ChatResponse } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: ChatResponse;
}

interface MessageBubbleProps {
  message: Message;
}

/**
 * Renders a single chat message.
 *
 * User messages: right-aligned, blue background.
 * Assistant messages: left-aligned, with confidence badge and source citations.
 */
export default function MessageBubble({ message }: MessageBubbleProps) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-xl">
          <div className="bg-brand-blue text-white rounded-2xl rounded-tr-sm px-4 py-3 text-sm leading-relaxed">
            {message.content}
          </div>
        </div>
      </div>
    );
  }

  // Assistant message
  return (
    <div className="flex items-start gap-3">
      {/* Avatar */}
      <div
        className="w-8 h-8 rounded-full bg-brand-blue flex items-center justify-center flex-shrink-0 mt-1"
        aria-hidden="true"
      >
        <span className="text-white text-xs font-bold">AI</span>
      </div>

      {/* Message content */}
      <div className="flex-1 min-w-0">
        <div className="bg-gray-50 border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3">
          {/* Answer text — preserve whitespace formatting */}
          <div className="text-sm text-gray-900 leading-relaxed whitespace-pre-wrap">
            {message.content}
          </div>

          {/* Confidence + sources */}
          {message.response && (
            <SourceCitation
              confidence={message.response.confidence}
              sources={message.response.sources}
              disclaimer={message.response.disclaimer}
            />
          )}
        </div>
      </div>
    </div>
  );
}
