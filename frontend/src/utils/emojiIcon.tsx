import type { CSSProperties } from "react";
import {
  BarChart3, Brain, Building2, CheckCircle2, ClipboardList, Flame, FlaskConical,
  FolderKanban, Hourglass, Laptop, Microscope, Package, PauseCircle, Palette,
  Plug, RefreshCw, Rocket, Ruler, Search, Settings2, Shapes, Sparkles, Star,
  Target, Wrench, Zap,
} from "lucide-react";

// Bo'lim/ustun/profil uchun tanlangan emojiga mos lucide ikonka — admin
// panelida emoji o'rniga ko'rsatiladi (saqlanadigan qiymat o'zgarmaydi,
// chunki u Telegram xabarlarida ishlatiladi).
const EMOJI_ICONS: Record<string, typeof Shapes> = {
  "🆕": Sparkles,
  "🔄": RefreshCw,
  "🔍": Search,
  "✅": CheckCircle2,
  "⏸️": PauseCircle,
  "🚀": Rocket,
  "🧪": FlaskConical,
  "📦": Package,
  "🗂️": FolderKanban,
  "⏳": Hourglass,
  "📋": ClipboardList,
  "🔌": Plug,
  "💻": Laptop,
  "📐": Ruler,
  "🔧": Wrench,
  "🎨": Palette,
  "🏢": Building2,
  "🔬": Microscope,
  "⚙️": Settings2,
  "📊": BarChart3,
  "🎯": Target,
  "⚡": Zap,
  "🧠": Brain,
  "🔥": Flame,
  "🌟": Star,
};

interface EmojiIconProps {
  emoji?: string | null;
  size?: number;
  color?: string;
  style?: CSSProperties;
}

export function EmojiIcon({ emoji, size = 16, color, style }: EmojiIconProps) {
  const Icon = (emoji && EMOJI_ICONS[emoji]) || Shapes;
  return <Icon size={size} color={color} style={style} />;
}
