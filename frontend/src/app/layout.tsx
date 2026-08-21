import type { Metadata } from "next";
import "./globals.css";
import Navbar from "../components/layout/Navbar";
import Sidebar from "../components/layout/Sidebar";
import MobileNav from "../components/layout/MobileNav";
import { AuthProvider } from "../context/AuthContext";
import TerminalGate from "../components/auth/TerminalGate";

export const metadata: Metadata = {
  title: "Tradly — AI/ML Forex Market Intelligence Platform",
  description: "Institutional-grade Forex market intelligence, technical analysis, RAG AI assistant, and pip-accurate paper trading simulator.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-tradly-bg text-tradly-text min-h-screen flex flex-col antialiased selection:bg-cyan-500 selection:text-black">
        <AuthProvider>
          <TerminalGate>
            <Navbar />
            <div className="flex flex-1 overflow-hidden relative">
              <Sidebar />
              <main className="flex-1 p-3 sm:p-6 pb-24 md:pb-6 overflow-y-auto max-w-7xl mx-auto w-full">
                {children}
              </main>
            </div>
            <MobileNav />
          </TerminalGate>
        </AuthProvider>
      </body>
    </html>
  );
}
