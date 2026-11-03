import { useQuery } from "@tanstack/react-query";
import { FileText, MessageSquare, Search, CheckCircle2, Clock, AlertCircle } from "lucide-react";
import { dashboardService } from "@/services/dashboard.service";
import { useAuthStore } from "@/store/authStore";
import { useNavigate } from "react-router-dom";

function StatCard({
  icon: Icon,
  label,
  value,
  color = "text-primary",
}: {
  icon: React.ElementType;
  label: string;
  value: number | string;
  color?: string;
}) {
  return (
    <div className="bg-card border border-border rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-medium text-muted-foreground">{label}</span>
        <div className={`w-9 h-9 rounded-lg bg-muted flex items-center justify-center ${color}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <p className="text-3xl font-bold text-foreground">{value}</p>
    </div>
  );
}

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();

  const { data: stats, isLoading } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: dashboardService.getStats,
  });

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Welcome */}
      <div>
        <h2 className="text-2xl font-bold text-foreground">
          Welcome back{user?.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}
        </h2>
        <p className="text-muted-foreground mt-1">
          Here's an overview of your KnowledgeHub activity.
        </p>
      </div>

      {/* Stats grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-card border border-border rounded-xl p-6 animate-pulse h-28" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard
            icon={FileText}
            label="Total Documents"
            value={stats?.total_documents ?? 0}
          />
          <StatCard
            icon={MessageSquare}
            label="Conversations"
            value={stats?.total_conversations ?? 0}
            color="text-blue-500"
          />
          <StatCard
            icon={Search}
            label="Total Queries"
            value={stats?.total_queries ?? 0}
            color="text-green-500"
          />
        </div>
      )}

      {/* Document status breakdown */}
      {stats && (
        <div className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-sm font-semibold text-foreground mb-4">
            Document Processing Status
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { key: "completed", label: "Completed", Icon: CheckCircle2, color: "text-green-500" },
              { key: "processing", label: "Processing", Icon: Clock, color: "text-yellow-500" },
              { key: "pending", label: "Pending", Icon: Clock, color: "text-muted-foreground" },
              { key: "failed", label: "Failed", Icon: AlertCircle, color: "text-destructive" },
            ].map(({ key, label, Icon, color }) => (
              <div key={key} className="flex items-center gap-3">
                <Icon className={`w-5 h-5 ${color}`} />
                <div>
                  <p className="text-xs text-muted-foreground">{label}</p>
                  <p className="text-lg font-semibold text-foreground">
                    {stats.documents_by_status[key] ?? 0}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <button
          onClick={() => navigate("/documents")}
          className="bg-card border border-border rounded-xl p-6 text-left hover:border-primary/50 hover:bg-accent transition-colors group"
        >
          <FileText className="w-8 h-8 text-primary mb-3" />
          <h3 className="font-semibold text-foreground">Upload Document</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Add a new PDF to your knowledge base
          </p>
        </button>
        <button
          onClick={() => navigate("/conversations")}
          className="bg-card border border-border rounded-xl p-6 text-left hover:border-primary/50 hover:bg-accent transition-colors group"
        >
          <MessageSquare className="w-8 h-8 text-blue-500 mb-3" />
          <h3 className="font-semibold text-foreground">Start a Conversation</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Ask questions about your documents
          </p>
        </button>
      </div>
    </div>
  );
}
