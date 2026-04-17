"use client";

import { useState, useRef, useEffect } from "react";
import { queryDocument } from "@/lib/api";
import { ChatMessage, QueryResponse } from "@/types";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { ComplianceStatusBadge } from "./ComplianceStatusBadge";
import { Send, AlertTriangle, User, Bot } from "lucide-react";

interface Props {
  documentId: string;
  onNewResponse: (response: QueryResponse) => void;
}

const SUGGESTED_QUERIES = [
  "Does this document meet ADA accessible route requirements?",
  "Are the wall insulation R-values compliant with ASHRAE 90.1?",
  "Does the fall protection plan meet OSHA 1926.502 requirements?",
  "Are the egress stairs compliant with IBC riser and tread requirements?",
];

export function ChatInterface({ documentId, onNewResponse }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return;
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);
    try {
      const response = await queryDocument(documentId, text);
      onNewResponse(response);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: response.answer,
          response,
          timestamp: new Date(),
        },
      ]);
    } catch (err: unknown) {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `Error: ${err instanceof Error ? err.message : "Query failed"}`,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-5">
        {messages.length === 0 && (
          <div className="py-6">
            <p className="text-xs font-semibold text-ink-muted uppercase tracking-wider mb-3">
              Suggested queries
            </p>
            <div className="grid gap-2">
              {SUGGESTED_QUERIES.map((q) => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  className="text-left text-sm text-ink-secondary bg-surface-secondary hover:bg-brand-blue-light border border-border hover:border-brand-blue rounded-lg px-4 py-2.5 transition-colors group"
                >
                  <span className="group-hover:text-brand-blue transition-colors">{q}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
            {/* Avatar */}
            <div
              className={`w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center mt-0.5
                ${msg.role === "user"
                  ? "bg-brand-blue"
                  : "bg-surface-secondary border border-border"
                }`}
            >
              {msg.role === "user" ? (
                <User className="w-3.5 h-3.5 text-white" />
              ) : (
                <Bot className="w-3.5 h-3.5 text-brand-blue" />
              )}
            </div>

            {/* Bubble */}
            <div className={`max-w-[80%] ${msg.role === "user" ? "items-end" : "items-start"} flex flex-col gap-2`}>
              {msg.role === "assistant" && msg.response && (
                <div className="flex flex-wrap gap-1.5">
                  <ComplianceStatusBadge status={msg.response.compliance_status} />
                  <ConfidenceBadge confidence={msg.response.confidence} />
                </div>
              )}

              {msg.response?.hallucination_warning && (
                <div className="flex items-start gap-2 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-lg p-2.5">
                  <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-amber-500" />
                  <span>{msg.response.hallucination_warning}</span>
                </div>
              )}

              <div
                className={`rounded-xl px-4 py-3 text-sm leading-relaxed shadow-card
                  ${msg.role === "user"
                    ? "bg-brand-blue text-white"
                    : "bg-white border border-border text-ink"
                  }`}
              >
                {msg.content}
              </div>

              <span className="text-xs text-ink-subtle px-1">
                {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </span>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-full bg-surface-secondary border border-border flex-shrink-0 flex items-center justify-center">
              <Bot className="w-3.5 h-3.5 text-brand-blue" />
            </div>
            <div className="bg-white border border-border rounded-xl px-4 py-3 shadow-card">
              <div className="flex gap-1.5 items-center h-4">
                {[0, 150, 300].map((delay) => (
                  <div
                    key={delay}
                    className="w-1.5 h-1.5 bg-brand-blue rounded-full animate-bounce"
                    style={{ animationDelay: `${delay}ms` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-6 py-4 border-t border-border bg-surface-secondary">
        <div className="flex gap-2.5">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage(input)}
            placeholder="Ask a compliance question about this document..."
            className="flex-1 bg-white border border-border rounded-lg px-4 py-2.5 text-sm text-ink placeholder-ink-subtle focus:outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/10 transition-all"
            disabled={loading}
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || loading}
            className="bg-brand-blue hover:bg-brand-blue-dark disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-lg px-4 py-2.5 transition-colors shadow-card flex items-center gap-2 font-medium text-sm"
          >
            <Send className="w-4 h-4" />
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
