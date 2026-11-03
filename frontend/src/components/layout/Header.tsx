import { useAuthStore } from "@/store/authStore";
import { useLocation } from "react-router-dom";

const pageTitles: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/documents": "Documents",
  "/conversations": "Conversations",
};

export default function Header() {
  const user = useAuthStore((s) => s.user);
  const location = useLocation();

  const title =
    pageTitles[location.pathname] ??
    (location.pathname.startsWith("/conversations/") ? "Conversation" : "KnowledgeHub AI");

  return (
    <header className="h-14 border-b border-border bg-card px-6 flex items-center justify-between shrink-0">
      <h1 className="text-base font-semibold text-foreground">{title}</h1>

      {user && (
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
            <span className="text-xs font-semibold text-primary-foreground">
              {user.full_name.slice(0, 1).toUpperCase()}
            </span>
          </div>
          <span className="text-sm text-muted-foreground hidden sm:block">
            {user.full_name}
          </span>
        </div>
      )}
    </header>
  );
}
