"use client";

import React from 'react';
import Link from 'next/link';
import {
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
  { href: "/pvt-calculations", icon: Droplets, label: "PVT Calculations" }, // Added new link
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
// Removed Button and Chevron imports as the toggle is now only in Header
// import { Button } from '@/components/ui/button';
// import { ChevronLeft, ChevronRight } from 'lucide-react';

interface SidebarProps {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

export default function Sidebar({ sidebarOpen, setSidebarOpen }: SidebarProps) {
  return (
    <TooltipProvider delayDuration={0}>
      <aside
        className={cn(
          "flex-col h-full bg-card border-r border-border transition-all duration-300 ease-in-out",
          sidebarOpen ? "flex w-64" : "w-20 hidden md:flex" // Manages width and mobile visibility
        )}
      >
        {/* Sidebar header: Displays logo/title. Toggle is in Header.tsx. */}
        <div className={cn(
          "flex items-center p-4 border-b border-border",
          sidebarOpen ? "justify-between" : "justify-center"
        )}>
          <Link href="/" className="flex items-center space-x-2">
            <Image
              src="/placeholder-logo.svg"
              alt="PetroLúmen Logo"
              width={sidebarOpen ? 32 : 28}
              height={sidebarOpen ? 32 : 28}
              className={sidebarOpen ? "w-8 h-8" : "w-7 h-7"}
            />
            {sidebarOpen && (
              <span className="text-xl font-semibold text-foreground">
                PetroLúmen
              </span>
            )}
          </Link>
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
