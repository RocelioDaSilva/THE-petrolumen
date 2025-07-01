import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider";
import Sidebar from "@/app/components/Sidebar"; // Import the Sidebar component

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Petroleum Engineering Platform",
  description: "Advanced petroleum engineering analysis and simulation platform",
    generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider 
          attribute="class" 
          defaultTheme="system" 
          enableSystem 
          disableTransitionOnChange
        >
          <div className="flex min-h-screen bg-background">
            <Sidebar />
            <main className="flex-1 p-4 md:p-6 lg:p-8">
              {/* Added padding to the main content area */}
              {children}
            </main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  )
}
