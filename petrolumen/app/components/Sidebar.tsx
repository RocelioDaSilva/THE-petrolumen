"use client";

import React from 'react'; // Removed useState as it's now controlled by layout
import Link from 'next/link';
// Image component for logo is in Header.tsx, so not needed here unless we want a different logo/title presentation when expanded.
// For now, the Header component handles the main logo and title.
import {
  // ChevronLeft, // Controlled by Header
  // ChevronRight, // Controlled by Header
  LayoutDashboard,
  Droplets,
  LineChart,
  Settings,
  Sliders,
  Database,
  Brain,
  Users,
  FileText,
  HelpCircle
} from 'lucide-react';
// Button for toggle is in Header.tsx
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface NavItem {
  href: string;
  icon: React.ElementType;
  label: string;
  disabled?: boolean;
}

const navItems: NavItem[] = [
  { href: "/", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/simulation", icon: Droplets, label: "Reservoir Simulation" },
  { href: "/production", icon: LineChart, label: "Production Analysis" },
  { href: "/optimization", icon: Sliders, label: "Optimization" },
  { href: "/data-management", icon: Database, label: "Data Management" },
  { href: "/ai-analytics", icon: Brain, label: "AI Analytics" },
  { href: "/user-management", icon: Users, label: "User Management", disabled: true },
  { href: "/reports", icon: FileText, label: "Reports", disabled: true },
  { href: "/settings", icon: Settings, label: "Settings" },
  { href: "/help", icon: HelpCircle, label: "Help & Documentation" },
];

import Image from 'next/image'; // Added Image import
import { Button } from '@/components/ui/button'; // Added Button import
import { ChevronLeft, ChevronRight } from 'lucide-react'; // Added Chevron imports

interface SidebarProps {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

export default function Sidebar({ sidebarOpen, setSidebarOpen }: SidebarProps) {
  // Removed internal isCollapsed state and toggleSidebar function
  // The state is now controlled by RootLayout

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        className={cn(
          "flex-col h-full bg-card border-r border-border transition-all duration-300 ease-in-out",
          // Use flex only if sidebarOpen is true, otherwise it might take space when hidden by other means
          // Or, use conditional rendering in layout if it should be completely removed from DOM
          sidebarOpen ? "flex w-64" : "w-20 hidden md:flex" // Adjust visibility for mobile if needed
        )}
      >
        {/* Header section of the sidebar, including toggle */}
        {/* The main toggle is now in Header.tsx, this can be a secondary or removed if Header is always visible */}
        {/* For this example, let's assume the toggle here is for a different style or if Header is not used */}
        {/* If the toggle is only in Header.tsx, this internal button should be removed. */}
        {/* Based on RootLayout, the toggle is in Header. This button is redundant or for a different UX. */}
        {/* For now, let's keep it but have it use the passed setSidebarOpen */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          {!sidebarOpen && ( // Show only icon when collapsed, or full logo when expanded
            <Link href="/" className="flex items-center justify-center w-full">
              <Image src="/placeholder-logo.svg" alt="PetroLúmen Icon" width={28} height={28} className="w-7 h-7" />
            </Link>
          )}
          {sidebarOpen && (
            <Link href="/" className="flex items-center space-x-2">
              <Image src="/placeholder-logo.svg" alt="PetroLúmen" width={32} height={32} className="w-8 h-8" />
              <span className="text-xl font-semibold text-foreground">PetroLúmen</span>
            </Link>
          )}
           {/* This button is likely redundant if Header.tsx has the main toggle.
               If kept, it should use the props. If sidebarOpen can only be controlled by Header, remove this.
               Let's assume for now it's a way to also control it from within the sidebar itself.
            */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-muted-foreground hover:text-foreground md:hidden" // Example: hide on md+, assuming Header toggle is primary
          >
            {sidebarOpen ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
            <span className="sr-only">{sidebarOpen ? "Collapse Sidebar" : "Expand Sidebar"}</span>
          </Button>
        </div>

        <nav className="flex-grow px-2 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <Tooltip key={item.label}>
              <TooltipTrigger asChild>
                <Link
                  href={item.disabled ? "#" : item.href}
                  className={cn(
                    "flex items-center px-3 py-2.5 rounded-md text-sm font-medium transition-colors",
                    "text-muted-foreground hover:bg-muted hover:text-foreground",
                    item.disabled && "opacity-50 cursor-not-allowed"
                    // Add active link styling if needed, e.g., based on current path
                  )}
                  aria-disabled={item.disabled}
                  onClick={(e) => item.disabled && e.preventDefault()}
                >
                  <item.icon className={cn("w-5 h-5", sidebarOpen ? "mr-3" : "mx-auto")} />
                  {sidebarOpen && <span>{item.label}</span>}
                </Link>
              </TooltipTrigger>
              {!sidebarOpen && ( // Show tooltip only when sidebar is collapsed
                <TooltipContent side="right">
                  {item.label}
                </TooltipContent>
              )}
            </Tooltip>
          ))}
        </nav>

        {sidebarOpen && ( // Show footer only when sidebar is expanded
          <div className="p-4 mt-auto border-t border-border">
            <p className="text-xs text-center text-muted-foreground">
              © {new Date().getFullYear()} PetroLúmen
            </p>
          </div>
        )}
      </aside>
    </TooltipProvider>
  );
}
