"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";
import { chatAPI, type ChatRequest, type ChatResponse, type VisaType } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: ChatResponse;
}

interface ChatInterfaceProps {
  visaType: VisaType;
}

/**
 * Main chat interface component.
 *
 * Maintains message history, handles user input, and calls the backend
 * /chat endpoint. Shows a loading indicator while waiting for responses.
 *
 * Conversation continuity: tracks conversation_id from the first response
 * and passes it back on subsequent requests.
 */
export default function ChatInterface({ visaType }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmedInput = input.trim();
    if (!trimmedInput || isLoading) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmedInput,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setError(null);

    try {
      const request: ChatRequest = {
        visa_type: visaType,
        message: trimmedInput,
        conversation_id: conversationId,
      };

      const response = await chatAPI(request);

      // Persist conversation ID for follow-up questions
      if (!conversationId) {
        setConversationId(response.conversation_id);
      }

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.answer,
        response,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "An unexpected error occurred";
      setError(
        message.includes("503")
          ? "The AI service is temporarily unavailable. Please check that the backend is running and your API key is set."
          : `Error: ${message}`
      );
    } finally {
      setIsLoading(false);
      // Re-focus input after response
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Enter (without Shift for newline)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSubmit(e as unknown as FormEvent);
    }
  };

  return (
    <div className="flex flex-col" style={{ height: "calc(100vh - 280px)", minHeight: "400px" }}>
      {/* Message history */}
      <div className="flex-1 overflow-y-auto chat-scroll space-y-4 mb-4 pr-1">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-16">
            <p className="text-lg mb-2">Ask me anything about your visa</p>
            <p className="text-sm">
              Questions about work rights, switching employers, salary thresholds,
              or path to ILR — I&apos;ll answer based on your visa type.
            </p>
          </div>
        )}

        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-brand-blue flex items-center justify-center flex-shrink-0">
              <span className="text-white text-xs font-bold">AI</span>
            </div>
            <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0ms]" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:150ms]" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
            <strong>Error:</strong> {error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input form */}
      <form onSubmit={handleSubmit} className="border-t border-gray-200 pt-4">
        <div className="flex gap-3 items-end">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your visa rights, work conditions, or migration questions..."
            disabled={isLoading}
            rows={2}
            maxLength={2000}
            className="flex-1 resize-none rounded-lg border border-gray-300 px-4 py-3 text-sm
                       focus:outline-none focus:ring-2 focus:ring-brand-blue focus:border-transparent
                       disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Your question"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-5 py-3 bg-brand-blue text-white rounded-lg font-medium text-sm
                       hover:bg-brand-blue-dark transition-colors
                       focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-offset-2
                       disabled:opacity-50 disabled:cursor-not-allowed
                       flex-shrink-0"
            aria-label="Send message"
          >
            {isLoading ? "..." : "Send"}
          </button>
        </div>
        <p className="mt-2 text-xs text-gray-400 text-right">
          Press Enter to send · Shift+Enter for newline
        </p>
      </form>
    </div>
  );
}
