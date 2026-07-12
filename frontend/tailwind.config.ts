import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // ── Color System ──────────────────────────────────────────────
      colors: {
        // Semantic tokens (mapped to CSS variables for dark mode)
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",

        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
          50: "hsl(var(--primary-50))",
          100: "hsl(var(--primary-100))",
          200: "hsl(var(--primary-200))",
          600: "hsl(var(--primary-600))",
          700: "hsl(var(--primary-700))",
          900: "hsl(var(--primary-900))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },

        // Semantic status colors
        success: {
          DEFAULT: "hsl(var(--success))",
          foreground: "hsl(var(--success-foreground))",
          50: "hsl(var(--success-50))",
        },
        warning: {
          DEFAULT: "hsl(var(--warning))",
          foreground: "hsl(var(--warning-foreground))",
          50: "hsl(var(--warning-50))",
        },
        info: {
          DEFAULT: "hsl(var(--info))",
          foreground: "hsl(var(--info-foreground))",
          50: "hsl(var(--info-50))",
        },

        // Track category colors
        track: {
          tech: "#6366f1",
          data: "#8b5cf6",
          design: "#ec4899",
          business: "#f59e0b",
        },
      },

      // ── Border Radius ─────────────────────────────────────────────
      borderRadius: {
        none: "0",
        sm: "4px",
        DEFAULT: "6px",
        md: "8px",
        lg: "12px",
        xl: "16px",
        "2xl": "24px",
        full: "9999px",
      },

      // ── Typography ────────────────────────────────────────────────
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
        mono: [
          "JetBrains Mono",
          "Fira Code",
          "Fira Mono",
          "Roboto Mono",
          "monospace",
        ],
      },
      fontSize: {
        "2xs": ["11px", { lineHeight: "1.4", letterSpacing: "0.02em" }],
        xs: ["12px", { lineHeight: "1.4", letterSpacing: "0.01em" }],
        sm: ["13px", { lineHeight: "1.5" }],
        base: ["14px", { lineHeight: "1.5" }],
        md: ["15px", { lineHeight: "1.6" }],
        lg: ["16px", { lineHeight: "1.6" }],
        xl: ["18px", { lineHeight: "1.5" }],
        "2xl": ["20px", { lineHeight: "1.4" }],
        "3xl": ["24px", { lineHeight: "1.3", letterSpacing: "-0.01em" }],
        "4xl": ["30px", { lineHeight: "1.2", letterSpacing: "-0.01em" }],
        "5xl": ["36px", { lineHeight: "1.15", letterSpacing: "-0.02em" }],
        "6xl": ["48px", { lineHeight: "1.1", letterSpacing: "-0.02em" }],
      },
      fontWeight: {
        normal: "400",
        medium: "500",
        semibold: "600",
        bold: "700",
        extrabold: "800",
      },

      // ── Spacing ───────────────────────────────────────────────────
      spacing: {
        "0.5": "2px",
        "1": "4px",
        "1.5": "6px",
        "2": "8px",
        "2.5": "10px",
        "3": "12px",
        "3.5": "14px",
        "4": "16px",
        "5": "20px",
        "6": "24px",
        "7": "28px",
        "8": "32px",
        "9": "36px",
        "10": "40px",
        "11": "44px",
        "12": "48px",
        "14": "56px",
        "16": "64px",
        "18": "72px",
        "20": "80px",
        "24": "96px",
        "28": "112px",
        "32": "128px",
        "36": "144px",
        "40": "160px",
        "48": "192px",
        "56": "224px",
        "64": "256px",
        "72": "288px",
        "80": "320px",
        "96": "384px",
      },

      // ── Shadows ───────────────────────────────────────────────────
      boxShadow: {
        xs: "0 1px 2px 0 rgb(0 0 0 / 0.04)",
        sm: "0 1px 3px 0 rgb(0 0 0 / 0.08), 0 1px 2px -1px rgb(0 0 0 / 0.06)",
        DEFAULT: "0 2px 4px 0 rgb(0 0 0 / 0.08), 0 1px 2px -1px rgb(0 0 0 / 0.06)",
        md: "0 4px 8px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.06)",
        lg: "0 10px 20px -3px rgb(0 0 0 / 0.1), 0 4px 8px -4px rgb(0 0 0 / 0.06)",
        xl: "0 20px 40px -5px rgb(0 0 0 / 0.12), 0 8px 16px -6px rgb(0 0 0 / 0.06)",
        "2xl": "0 25px 50px -12px rgb(0 0 0 / 0.25)",
        inner: "inset 0 2px 4px 0 rgb(0 0 0 / 0.06)",
        none: "none",
        // Card hover shadow
        card: "0 0 0 1px hsl(var(--border)), 0 4px 12px -2px rgb(0 0 0 / 0.08)",
        "card-hover": "0 0 0 1px hsl(var(--primary) / 0.3), 0 8px 24px -4px rgb(0 0 0 / 0.12)",
        // Focus ring
        focus: "0 0 0 3px hsl(var(--ring) / 0.35)",
      },

      // ── Animations ────────────────────────────────────────────────
      keyframes: {
        // Skeleton shimmer
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        // Smooth fade in
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        // Slide up for toasts on mobile
        "slide-up": {
          "0%": { transform: "translateY(100%)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        // Slide in from right for toasts on desktop
        "slide-in-right": {
          "0%": { transform: "translateX(120%)", opacity: "0" },
          "100%": { transform: "translateX(0)", opacity: "1" },
        },
        // Slide in from top for navbar
        "slide-down": {
          "0%": { transform: "translateY(-100%)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        // Pulse for badge
        "pulse-soft": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.7" },
        },
        // Progress bar fill
        "progress-fill": {
          "0%": { width: "0%" },
          "100%": { width: "var(--progress-width, 100%)" },
        },
        // Celebration confetti drop
        "confetti-drop": {
          "0%": { transform: "translateY(-10px) rotate(0deg)", opacity: "1" },
          "100%": { transform: "translateY(100vh) rotate(720deg)", opacity: "0" },
        },
        // Spin for loaders
        spin: {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
        // Scale up for modals
        "scale-in": {
          "0%": { transform: "scale(0.95)", opacity: "0" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
        // Typing indicator dots
        "bounce-dot": {
          "0%, 80%, 100%": { transform: "scale(0.8)", opacity: "0.5" },
          "40%": { transform: "scale(1)", opacity: "1" },
        },
      },
      animation: {
        shimmer: "shimmer 1.8s ease-in-out infinite",
        "fade-in": "fade-in 0.2s ease-out",
        "slide-up": "slide-up 0.3s ease-out",
        "slide-in-right": "slide-in-right 0.3s ease-out",
        "slide-down": "slide-down 0.3s ease-out",
        "pulse-soft": "pulse-soft 2s ease-in-out infinite",
        "progress-fill": "progress-fill 0.8s ease-out forwards",
        spin: "spin 0.8s linear infinite",
        "scale-in": "scale-in 0.2s ease-out",
        "bounce-dot": "bounce-dot 1.2s ease-in-out infinite",
      },
      transitionDuration: {
        "0": "0ms",
        "150": "150ms",
        "200": "200ms",
        "300": "300ms",
        "500": "500ms",
        "700": "700ms",
      },
      transitionTimingFunction: {
        smooth: "cubic-bezier(0.4, 0, 0.2, 1)",
        bounce: "cubic-bezier(0.34, 1.56, 0.64, 1)",
        sharp: "cubic-bezier(0.4, 0, 1, 1)",
      },

      // ── Screens ───────────────────────────────────────────────────
      screens: {
        xs: "475px",
        sm: "640px",
        md: "768px",
        lg: "1024px",
        xl: "1280px",
        "2xl": "1440px",
      },

      // ── Max widths ────────────────────────────────────────────────
      maxWidth: {
        "8xl": "1400px",
        "9xl": "1600px",
        content: "720px",
        prose: "65ch",
      },

      // ── Z-index scale ─────────────────────────────────────────────
      zIndex: {
        "0": "0",
        "10": "10",
        "20": "20",
        "30": "30",
        "40": "40",
        "50": "50",
        "60": "60",
        "70": "70",
        "80": "80",
        "90": "90",
        "100": "100",
        navbar: "50",
        sidebar: "40",
        drawer: "60",
        modal: "70",
        toast: "80",
        tooltip: "90",
      },

      // ── Grid ──────────────────────────────────────────────────────
      gridTemplateColumns: {
        "sidebar-content": "240px 1fr",
        "sidebar-content-lg": "280px 1fr",
        "course-detail": "1fr 360px",
      },
    },
  },
  plugins: [],
};

export default config;
