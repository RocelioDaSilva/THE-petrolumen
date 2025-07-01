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

export default function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        className={cn(
          "flex flex-col h-screen bg-gray-100 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 transition-all duration-300 ease-in-out",
          isCollapsed ? "w-20" : "w-64"
        )}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          {!isCollapsed && (
            <Link href="/" className="flex items-center space-x-2">
              <Image src="/placeholder-logo.svg" alt="PetroLúmen" width={32} height={32} className="w-8 h-8" />
              <span className="text-xl font-semibold text-gray-800 dark:text-white">PetroLúmen</span>
            </Link>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
          >
            {isCollapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
            <span className="sr-only">{isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}</span>
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
                    "text-gray-700 hover:bg-gray-200 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:text-white",
                    item.disabled && "opacity-50 cursor-not-allowed"
                  )}
                  aria-disabled={item.disabled}
                  onClick={(e) => item.disabled && e.preventDefault()}
                >
                  <item.icon className={cn("w-5 h-5", isCollapsed ? "mx-auto" : "mr-3")} />
                  {!isCollapsed && <span>{item.label}</span>}
                </Link>
              </TooltipTrigger>
              {isCollapsed && (
                <TooltipContent side="right">
                  {item.label}
                </TooltipContent>
              )}
            </Tooltip>
          ))}
        </nav>

        {!isCollapsed && (
          <div className="p-4 mt-auto border-t border-gray-200 dark:border-gray-700">
            <p className="text-xs text-center text-gray-500 dark:text-gray-400">
              © {new Date().getFullYear()} PetroLúmen
            </p>
          </div>
        )}
      </aside>
    </TooltipProvider>
  );
}
