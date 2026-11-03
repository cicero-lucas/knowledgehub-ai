import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  FileText,
  Trash2,
  RefreshCw,
  Loader2,
  CloudUpload,
} from "lucide-react";
import { documentsService } from "@/services/documents.service";
import { formatBytes, formatDate } from "@/lib/utils";
import type { Document } from "@/types";

function StatusBadge({ status }: { status: Document["status"] }) {
  const map: Record<Document["status"], { dot: string; label: string; cls: string }> = {
    completed: { dot: "●", label: "Completed", cls: "text-green-700 bg-green-50 border border-green-200" },
    processing: { dot: "◉", label: "Processing", cls: "text-yellow-700 bg-yellow-50 border border-yellow-200" },
    pending:    { dot: "○", label: "Pending",    cls: "text-gray-500 bg-gray-50 border border-gray-200" },
    failed:     { dot: "✕", label: "Failed",     cls: "text-red-700 bg-red-50 border border-red-200" },
  };
  const { dot, label, cls } = map[status];
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-full ${cls}`}>
      {dot} {label}
    </span>
  );
}

export default function DocumentsPage() {
  const [uploadError, setUploadError] = useState("");
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["documents"],
    queryFn: () => documentsService.list(),
    refetchInterval: (query) => {
      // Poll while any document is processing/pending
      const items = query.state.data?.items ?? [];
      return items.some((d) => d.status === "processing" || d.status === "pending")
        ? 3000
        : false;
    },
  });

  const uploadMutation = useMutation({
    mutationFn: documentsService.upload,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
      setUploadError("");
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setUploadError(msg ?? "Upload failed.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: documentsService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
    },
  });

  const reprocessMutation = useMutation({
    mutationFn: documentsService.reprocess,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
  });

  const onDrop = useCallback(
    (accepted: File[]) => {
      accepted.forEach((file) => uploadMutation.mutate(file));
    },
    [uploadMutation]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    multiple: true,
  });

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Upload zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${
          isDragActive
            ? "border-primary bg-primary/5"
            : "border-border hover:border-primary/50 hover:bg-accent"
        }`}
      >
        <input {...getInputProps()} />
        <CloudUpload className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
        <p className="text-sm font-medium text-foreground">
          {isDragActive ? "Drop your PDFs here" : "Drag & drop PDFs here"}
        </p>
        <p className="text-xs text-muted-foreground mt-1">or click to browse — max 50MB per file</p>
      </div>

      {uploadMutation.isPending && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="w-4 h-4 animate-spin" />
          Uploading…
        </div>
      )}

      {uploadError && (
        <p className="text-sm text-destructive">{uploadError}</p>
      )}

      {/* Document list */}
      <div>
        <h2 className="text-sm font-semibold text-foreground mb-3">
          Your Documents ({data?.total ?? 0})
        </h2>

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-card border border-border rounded-xl h-16 animate-pulse" />
            ))}
          </div>
        ) : data?.items.length === 0 ? (
          <div className="bg-card border border-border rounded-xl p-12 text-center">
            <FileText className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
            <p className="text-sm text-muted-foreground">No documents yet. Upload your first PDF above.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {data?.items.map((doc) => (
              <div
                key={doc.id}
                className="bg-card border border-border rounded-xl px-5 py-4 flex items-center gap-4"
              >
                <FileText className="w-8 h-8 text-primary shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">
                    {doc.original_name}
                  </p>
                  <div className="flex items-center gap-3 mt-0.5">
                    <span className="text-xs text-muted-foreground">
                      {formatBytes(doc.file_size)}
                    </span>
                    {doc.page_count && (
                      <span className="text-xs text-muted-foreground">
                        {doc.page_count} pages
                      </span>
                    )}
                    <span className="text-xs text-muted-foreground">
                      {formatDate(doc.created_at)}
                    </span>
                  </div>
                </div>
                <StatusBadge status={doc.status} />
                <div className="flex items-center gap-1">
                  {doc.status === "failed" && (
                    <button
                      onClick={() => reprocessMutation.mutate(doc.id)}
                      disabled={reprocessMutation.isPending}
                      className="p-1.5 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
                      title="Reprocess"
                    >
                      <RefreshCw className="w-4 h-4" />
                    </button>
                  )}
                  <button
                    onClick={() => {
                      if (confirm(`Delete "${doc.original_name}"?`)) {
                        deleteMutation.mutate(doc.id);
                      }
                    }}
                    disabled={deleteMutation.isPending}
                    className="p-1.5 rounded-md hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
