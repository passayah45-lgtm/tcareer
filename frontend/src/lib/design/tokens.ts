/**
 * T-Career Design Tokens
 *
 * Single source of truth for design decisions used in components.
 * All values match the CSS custom properties in globals.css and
 * the Tailwind config extensions.
 *
 * Usage:
 *   import { cn, badge, button } from "@/lib/design/tokens";
 *   <div className={cn(card.base, card.hover)}>
 */

// ── Class name merger ──────────────────────────────────────────────────────
export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(" ").trim();
}

// ── Button variants ────────────────────────────────────────────────────────
export const button = {
  base: "inline-flex items-center justify-center gap-2 font-medium rounded transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none select-none whitespace-nowrap",

  // Sizes
  sm:   "h-8 px-3 text-xs",
  md:   "h-10 px-4 text-sm",
  lg:   "h-12 px-6 text-base",
  icon: "h-10 w-10 p-0",
  "icon-sm": "h-8 w-8 p-0",

  // Variants
  primary:     "bg-primary text-primary-foreground hover:bg-primary-600 active:bg-primary-700",
  secondary:   "bg-transparent text-foreground border border-border hover:bg-muted",
  ghost:       "bg-transparent text-foreground hover:bg-muted border-0",
  destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
  success:     "bg-success text-white hover:bg-success/90",
  link:        "bg-transparent text-primary hover:underline p-0 h-auto font-normal",
} as const;

// ── Card variants ──────────────────────────────────────────────────────────
export const card = {
  base:    "bg-card border border-border rounded-lg",
  shadow:  "shadow-xs",
  hover:   "transition-all duration-200 hover:shadow-md hover:-translate-y-0.5 cursor-pointer",
  padSm:   "p-4",
  padMd:   "p-5",
  padLg:   "p-8",
} as const;

// ── Badge variants ─────────────────────────────────────────────────────────
export const badge = {
  base: "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium leading-none whitespace-nowrap",
  default:     "bg-muted text-muted-foreground",
  primary:     "bg-primary/10 text-primary",
  success:     "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400",
  warning:     "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400",
  error:       "bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400",
  info:        "bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400",
  beginner:    "bg-emerald-50 text-emerald-700",
  intermediate:"bg-amber-50 text-amber-700",
  advanced:    "bg-red-50 text-red-700",
} as const;

// ── Input variants ─────────────────────────────────────────────────────────
export const input = {
  base:  "w-full h-10 px-3 text-sm rounded border border-input bg-background text-foreground placeholder:text-muted-foreground transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed",
  error: "border-destructive focus:ring-destructive",
  sm:    "h-8 px-2.5 text-xs",
  lg:    "h-12 px-4 text-base",
} as const;

// ── Typography scale ───────────────────────────────────────────────────────
export const text = {
  // Display
  "display-xl": "text-5xl font-bold tracking-tight leading-none",
  "display-lg": "text-4xl font-bold tracking-tight",

  // Headings
  h1: "text-3xl font-bold tracking-tight",
  h2: "text-2xl font-bold tracking-tight",
  h3: "text-xl font-semibold",
  h4: "text-lg font-semibold",
  h5: "text-base font-semibold",
  h6: "text-sm font-semibold",

  // Body
  "body-lg": "text-base leading-relaxed",
  "body":    "text-sm leading-relaxed",
  "body-sm": "text-xs leading-relaxed",

  // Utility
  caption:   "text-xs text-muted-foreground",
  label:     "text-sm font-medium",
  mono:      "font-mono text-sm",
  muted:     "text-muted-foreground",
  error:     "text-destructive text-xs",
  success:   "text-success text-xs",
} as const;

// ── Avatar sizes ───────────────────────────────────────────────────────────
export const avatar = {
  base: "rounded-full overflow-hidden flex-shrink-0 bg-primary/10 flex items-center justify-center font-semibold text-primary",
  xs:   "w-6 h-6 text-[10px]",
  sm:   "w-8 h-8 text-xs",
  md:   "w-10 h-10 text-sm",
  lg:   "w-12 h-12 text-base",
  xl:   "w-16 h-16 text-lg",
  "2xl":"w-24 h-24 text-2xl",
} as const;

// ── Skeleton ───────────────────────────────────────────────────────────────
export const skeleton = {
  base: "rounded animate-shimmer bg-gradient-to-r from-muted via-border to-muted bg-[length:200%_100%]",
  text: "h-3.5 rounded",
  card: "rounded-lg",
  avatar: "rounded-full",
} as const;

// ── Progress ───────────────────────────────────────────────────────────────
export const progress = {
  track: "w-full bg-muted rounded-full overflow-hidden",
  sm:    "h-1",
  md:    "h-1.5",
  lg:    "h-2",
  fill:  "h-full bg-primary rounded-full transition-all duration-700",
  fillSuccess: "h-full bg-success rounded-full transition-all duration-700",
} as const;

// ── Status colors for job type badges ─────────────────────────────────────
export const jobTypeBadge: Record<string, string> = {
  full_time:  "bg-blue-50 text-blue-700",
  part_time:  "bg-purple-50 text-purple-700",
  contract:   "bg-orange-50 text-orange-700",
  freelance:  "bg-pink-50 text-pink-700",
  internship: "bg-emerald-50 text-emerald-700",
  remote:     "bg-teal-50 text-teal-700",
};

// ── Track category colors ──────────────────────────────────────────────────
export const trackColors: Record<string, string> = {
  "Tech and Engineering": "#6366f1",
  "Data and AI":          "#8b5cf6",
  "Design and Product":   "#ec4899",
  "Business and Marketing": "#f59e0b",
};

// ── Spacing scale (for JS usage) ──────────────────────────────────────────
export const spacing = {
  1:  "4px",
  2:  "8px",
  3:  "12px",
  4:  "16px",
  5:  "20px",
  6:  "24px",
  8:  "32px",
  10: "40px",
  12: "48px",
  16: "64px",
  20: "80px",
} as const;

// ── Animation classes ──────────────────────────────────────────────────────
export const animation = {
  fadeIn:      "animate-fade-in",
  slideUp:     "animate-slide-up",
  slideRight:  "animate-slide-in-right",
  scaleIn:     "animate-scale-in",
  shimmer:     "animate-shimmer",
  spin:        "animate-spin",
  pulseSoft:   "animate-pulse-soft",
} as const;

// ── Z-index scale ──────────────────────────────────────────────────────────
export const zIndex = {
  base:    "z-0",
  above:   "z-10",
  sticky:  "z-20",
  navbar:  "z-50",
  sidebar: "z-40",
  drawer:  "z-60",
  modal:   "z-70",
  toast:   "z-80",
  tooltip: "z-90",
} as const;


