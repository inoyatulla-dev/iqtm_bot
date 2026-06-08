import { useEffect, useState } from "react";
import { Section, Cell, Spinner } from "@telegram-apps/telegram-ui";
import { statsApi } from "../api/client";
import type { RatingRow, StatusCounts } from "../api/types";
import { useAuth } from "../store/auth";

export function StatsPage() {
  const { isBoss } = useAuth();
  const [counts, setCounts] = useState<StatusCounts | null>(null);
  const [rating, setRating] = useState<RatingRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const c = isBoss ? await statsApi.global() : await statsApi.me();
      setCounts(c);
      if (isBoss) setRating(await statsApi.rating());
      setLoading(false);
    })();
  }, [isBoss]);

  if (loading || !counts)
    return <div className="center-screen"><Spinner size="l" /></div>;

  const medal = (i: number) => ["🥇", "🥈", "🥉"][i] || `${i + 1}.`;

  return (
    <div style={{ paddingBottom: 80 }}>
      <Section header={isBoss ? "📊 Umumiy statistika" : "📊 Mening statistikam"}>
        <Cell after={String(counts.total)}>Jami vazifalar</Cell>
        <Cell after={String(counts.new)}>🆕 Yangi</Cell>
        <Cell after={String(counts.in_progress)}>🔄 Jarayonda</Cell>
        <Cell after={String(counts.review)}>🔍 Tekshiruvda</Cell>
        <Cell after={String(counts.done)}>✅ Bajarildi</Cell>
        <Cell after={String(counts.overdue)}>⚠️ Kechikkan</Cell>
      </Section>

      {isBoss && rating.length > 0 && (
        <Section header="🏆 Xodimlar reytingi">
          {rating.map((r, i) => (
            <Cell
              key={r.user_id}
              before={<span style={{ fontSize: 18 }}>{medal(i)}</span>}
              subtitle={`✅ ${r.done} · 🔄 ${r.active} · ⚠️ ${r.overdue}`}
            >
              {r.name}
            </Cell>
          ))}
        </Section>
      )}
    </div>
  );
}
