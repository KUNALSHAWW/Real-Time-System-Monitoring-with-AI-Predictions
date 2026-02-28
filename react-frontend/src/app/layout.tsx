import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import { AgentProvider } from "@/context/AgentContext";

export const metadata: Metadata = {
  title: "System Monitor — SaaS Dashboard",
  description: "Real-time system monitoring with AI-powered anomaly detection",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body>
        <AuthProvider>
          <AgentProvider>{children}</AgentProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
