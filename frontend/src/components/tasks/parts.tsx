import type { BoardColumn } from "../../api/types";

export function Avatar({
  name, photo, size = 24, title,
}: { name?: string | null; photo?: string | null; size?: number; title?: string }) {
  return (
    <span className="avatar-wrap" style={{ width: size, height: size }} title={title || name || undefined}>
      <span className="avatar" style={{ fontSize: Math.round(size * 0.42) }}>
        {photo ? <img src={photo} alt="" /> : (name || "?").slice(0, 1).toUpperCase()}
      </span>
    </span>
  );
}

/** Bir nechta mas'ulni ustma-ust avatar sifatida ko'rsatish */
export function AvatarStack({
  people, size = 26, max = 3,
}: { people: { name?: string | null; photo?: string | null }[]; size?: number; max?: number }) {
  if (!people.length) return <span className="muted-dash">—</span>;
  const shown = people.slice(0, max);
  const rest = people.length - shown.length;
  return (
    <span className="avatar-stack">
      {shown.map((p, i) => (
        <span key={i} className="avatar-stack__item" style={{ marginLeft: i ? -8 : 0, zIndex: max - i }}>
          <Avatar name={p.name} photo={p.photo} size={size} />
        </span>
      ))}
      {rest > 0 && (
        <span className="avatar-stack__more" style={{ width: size, height: size, marginLeft: -8 }}>
          +{rest}
        </span>
      )}
    </span>
  );
}

export function StatusPill({ column }: { column?: BoardColumn }) {
  if (!column) return <span className="muted-dash">—</span>;
  return (
    <span
      className="status-pill"
      style={{ color: column.color, background: `${column.color}22`, borderColor: `${column.color}55` }}
    >
      {column.name}
    </span>
  );
}
