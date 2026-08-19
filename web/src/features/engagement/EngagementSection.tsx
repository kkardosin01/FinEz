import { Card } from "@/components/ui/Card";
import { useEngagementSummary } from "./hooks";

export function EngagementSection() {
  const { data, isLoading } = useEngagementSummary();

  if (isLoading || !data) return null;

  const { streak, badges } = data;
  if (streak.current_streak === 0 && badges.length === 0) return null;

  return (
    <Card className="flex flex-wrap items-center gap-4">
      {streak.current_streak > 0 && (
        <div className="flex items-center gap-2">
          <span className="text-xl" aria-hidden>
            🔥
          </span>
          <div>
            <p className="text-sm font-semibold">
              {streak.current_streak} {streak.current_streak === 1 ? "dia" : "dias"} seguidos
            </p>
            <p className="text-xs text-fg-secondary">recorde: {streak.longest_streak}d</p>
          </div>
        </div>
      )}

      {badges.length > 0 && (
        <ul className="flex flex-wrap gap-2">
          {badges.map((badge) => (
            <li
              key={badge.id}
              title={badge.label}
              className="rounded-full bg-bg px-3 py-1 text-xs font-medium text-fg-secondary"
            >
              {badge.label}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
