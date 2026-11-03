import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { MessageSquare, Plus, Trash2, Clock } from "lucide-react";
import { conversationsService } from "@/services/conversations.service";
import { formatDate } from "@/lib/utils";

export default function ConversationsListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["conversations"],
    queryFn: () => conversationsService.list(),
  });

  const createMutation = useMutation({
    mutationFn: () => conversationsService.create({ title: "New conversation" }),
    onSuccess: (conv) => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      navigate(`/conversations/${conv.id}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: conversationsService.delete,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["conversations"] }),
  });

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-foreground">Conversations</h2>
          <p className="text-sm text-muted-foreground mt-0.5">
            Ask questions about your documents
          </p>
        </div>
        <button
          onClick={() => createMutation.mutate()}
          disabled={createMutation.isPending}
          className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          <Plus className="w-4 h-4" />
          New conversation
        </button>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2].map((i) => (
            <div key={i} className="bg-card border border-border rounded-xl h-16 animate-pulse" />
          ))}
        </div>
      ) : data?.items.length === 0 ? (
        <div className="bg-card border border-border rounded-xl p-12 text-center">
          <MessageSquare className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
          <p className="text-sm text-muted-foreground">
            No conversations yet. Create one to start asking questions.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {data?.items.map((conv) => (
            <div
              key={conv.id}
              className="bg-card border border-border rounded-xl px-5 py-4 flex items-center gap-4 hover:border-primary/40 cursor-pointer transition-colors group"
              onClick={() => navigate(`/conversations/${conv.id}`)}
            >
              <MessageSquare className="w-8 h-8 text-blue-500 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground truncate">
                  {conv.title ?? "Untitled conversation"}
                </p>
                <div className="flex items-center gap-3 mt-0.5">
                  <span className="text-xs text-muted-foreground flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatDate(conv.updated_at ?? conv.created_at)}
                  </span>
                  {conv.document_count > 0 && (
                    <span className="text-xs text-muted-foreground">
                      {conv.document_count} doc{conv.document_count !== 1 ? "s" : ""}
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  if (confirm("Delete this conversation?")) {
                    deleteMutation.mutate(conv.id);
                  }
                }}
                className="p-1.5 rounded-md opacity-0 group-hover:opacity-100 hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-all"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
