"use client"; // Required for useState

import type React from "react"; // Keep type React for children prop
import { useState } from "react"; // Import useState
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import Sidebar from "@/app/components/Sidebar";
import Header from "@/app/components/Header"; // Import the new Header component
import AuthInitializer from "@/components/AuthInitializer"; // Import the AuthInitializer

const inter = Inter({ subsets: ["latin"] });

// Note: This is a client component ("use client" is at the top).
// For Next.js App Router, static metadata should be exported from server components (e.g., a parent layout.tsx if this were nested,
// or this file if it were a server component). Dynamic metadata can be generated using generateMetadata.
// The commented-out metadata below would not work as expected in a client component.
// If metadata is required for this root layout, it should be re-evaluated based on Next.js App Router best practices.

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarOpen, setSidebarOpen] = useState(true); // Manage sidebar state here

  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <AuthInitializer />
          <div className="flex flex-col h-screen bg-background">
            <Header sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
            <div className="flex flex-1 overflow-hidden">
              <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} /> {/* Pass state to Sidebar */}
              <main className="flex-1 p-4 md:p-6 lg:p-8 overflow-auto">
                {children}
              </main>
            </div>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
