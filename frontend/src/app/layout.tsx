import type { Metadata } from "next";
import { Quicksand, Fredoka } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";

const quicksand = Quicksand({
  variable: "--font-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const fredoka = Fredoka({
  variable: "--font-heading",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});

export const metadata: Metadata = {
  title: "paperpilot",
  description: "Ask your research papers questions and get answers with exact citations.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${quicksand.variable} ${fredoka.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        {children}
        <Toaster richColors position="top-center" />
      </body>
    </html>
  );
}
