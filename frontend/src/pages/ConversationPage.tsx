import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Send, Loader2, BookOpen, FileText } from "lucide-react";
import { conversationsService } from "@/services/conversations.service";
import { cn, formatDate } from "@/lib/utils";
import type { Message } from "@/types";

function SourceCard({ source }: { source: Message["sources"][number] }) {
  return (
    <div className="flex items-start gap-2 bg-muted/50 rounded-md px-3 py-2 text-xs">
      <FileText className="w-3.5 h-3.5 text-muted-foreground mt-0.5 shrink-0" />
      <div>
        <span className="font-medium text-foreground">{source.document_name}</span>
        {source.page_number && (
          <span className="text-muted-foreground ml-1">· page {source.page_number}</span>
        )}
        {source.relevance_score && (
          <span className="text-muted-foreground ml-1">
            · {(source.relevance_score * 100).toFixed(0)}% match
          </span>
        )}
      </div>
    </div>
  );
}

function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <div className={cn("flex gap-3", isUser ? "flex-row-reverse" : "flex-row")}>
      {/* Avatar */}
      <div
        className={cn(
          "w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold shrink-0",
          isUser ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
        )}
      >
        {isUser ? "U" : "AI"}
      </div>

      {/* Bubble */}
      <div className={cn("max-w-[75%] space-y-2", isUser ? "items-end" : "items-start")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap",
            isUser
              ? "bg-primary text-primary-foreground rounded-tr-sm"
              : "bg-card border border-border text-foreground rounded-tl-sm"
          )}
        >
          {message.content}
        </div>

        {/* Sources */}
        {message.sources.length > 0 && (
          <div className="space-y-1">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <BookOpen className="w-3 h-3" />
              Sources
            </div>
            {message.sources.map((s) => (
              <SourceCard key={s.id} source={s} />
            ))}
          </div>
        )}

        <p className="text-xs text-muted-foreground px-1">
          {formatDate(message.created_at)}
          {message.latency_ms && (
            <span className="ml-2">· {message.latency_ms}ms</span>
          )}
        </p>
      </div>
    </div>
  );
}

export default function ConversationPage() {
  const { id } = useParams<{ id: string }>();
  const [question, setQuestion] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  const { data: conversation, isLoading } = useQuery({
    queryKey: ["conversation", id],
    queryFn: () => conversationsService.get(id!),
    enabled: !!id,
  });

  const askMutation = useMutation({
    mutationFn: (q: string) => conversationsService.ask(id!, q),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversation", id] });
      setQuestion("");
    },
  });

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation?.messages?.length, askMutation.isPending]);

  const handleSend = () => {
    if (!question.trim() || askMutation.isPending) return;
    askMutation.mutate(question.trim());
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto flex flex-col h-[calc(100vh-8rem)]">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-6 pb-4">
        {conversation?.messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <BookOpen className="w-12 h-12 text-muted-foreground mb-4" />
            <p className="text-foreground font-medium">Ask anything about your documents</p>
            <p className="text-sm text-muted-foreground mt-1">
              Responses are grounded in your uploaded PDFs with source citations.
            </p>
          </div>
        ) : (
          conversation?.messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))
        )}

        {/* Typing indicator */}
        {askMutation.isPending && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-xs font-semibold text-muted-foreground shrink-0">
              AI
            </div>
            <div className="bg-card border border-border rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1 items-center">
                <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce [animation-delay:0ms]" />
                <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce [animation-delay:150ms]" />
                <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-border pt-4 pb-2">
        {askMutation.isError && (
          <p className="text-xs text-destructive mb-2">
            Failed to get a response. Please try again.
          </p>
        )}
        <div className="flex gap-3 items-end">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={askMutation.isPending}
            rows={1}
            placeholder="Ask a question about your documents… (Enter to send)"
            className="flex-1 resize-none px-4 py-3 rounded-xl border border-input bg-background text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50 max-h-32 overflow-y-auto"
            style={{ minHeight: "48px" }}
          />
          <button
            onClick={handleSend}
            disabled={!question.trim() || askMutation.isPending}
            className="w-12 h-12 bg-primary text-primary-foreground rounded-xl flex items-center justify-center hover:bg-primary/90 transition-colors disabled:opacity-50 shrink-0 text-lg"
          >
            {askMutation.isPending ? "…" : "↑"}
          </button>
        </div>
        <p className="text-xs text-muted-foreground mt-2 text-center">
          Answers are based exclusively on your uploaded documents
        </p>
      </div>
    </div>
  );
}
