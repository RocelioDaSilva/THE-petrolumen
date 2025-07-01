"use client"; // Required for useState

import type React from "react"; // Keep type React for children prop
import { useState } from "react"; // Import useState
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import Sidebar from "@/app/components/Sidebar";
import Header from "@/app/components/Header"; // Import the new Header component

const inter = Inter({ subsets: ["latin"] });

// Metadata can remain as is, but Next.js might recommend moving it if all exports are client components.
// For now, let's keep it here. If issues arise, we can revisit.
// export const metadata: Metadata = { // Metadata type might need to be imported if not global
//   title: "PetroLúmen Platform",
//   description: "Advanced petroleum engineering analysis and simulation platform",
// };

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
