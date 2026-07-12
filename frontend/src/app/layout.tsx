import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/shared/Providers";
import { Footer } from "@/components/layout/Footer";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
  preload: true,
});

export const metadata: Metadata = {
  title: {
    default: "T-Career - Learn Skills, Earn Certificates, Get Hired",
    template: "%s | T-Career",
  },
  description:
    "T-Career is an AI-powered learning and career development platform. Learn in-demand skills, earn verified certificates, build your portfolio, and connect with employers.",
  keywords: [
    "online learning",
    "career development",
    "tech courses",
    "certificates",
    "AI tutor",
    "job portal",
    "career tracks",
  ],
  authors: [{ name: "T-Career" }],
  creator: "T-Career",
  openGraph: {
    type: "website",
    locale: "en_US",
    siteName: "T-Career",
    title: "T-Career - Learn Skills, Earn Certificates, Get Hired",
    description:
      "AI-powered learning and career development platform with verified certificates and direct recruiter connections.",
  },
  twitter: {
    card: "summary_large_image",
    title: "T-Career",
    description: "Learn skills. Earn certificates. Get hired.",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
    },
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0f172a" },
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning className={inter.variable}>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="font-sans antialiased bg-background text-foreground min-h-screen">
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>
        <main id="main-content" tabIndex={-1}>
          <Providers>{children}</Providers>
        </main>
        <Footer />
      </body>
    </html>
  );
}
