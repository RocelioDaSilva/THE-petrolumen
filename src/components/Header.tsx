import React from "react";
import { Microscope, Wifi, Bell, User, Moon, Sun, Search, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface HeaderProps {
  activeModuleTitle: string;
  isDarkMode: boolean;
  onToggleTheme: () => void;
  onOpenSearch?: () => void;
}

export default function Header({
  activeModuleTitle,
  isDarkMode,
  onToggleTheme,
}: HeaderProps) {
  return (
    <header className="sticky top-0 z-30 bg-card/95 backdrop-blur-md border-b border-border shadow-xs">
      <div className="flex items-center justify-between px-6 py-3.5">
        {/* Brand & Breadcrumb */}
        <div className="flex items-center space-x-3.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
            <Microscope className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                PetroLúmen
              </h1>
              <Badge variant="outline" className="text-[10px] py-0 px-1.5 h-4 font-mono text-muted-foreground border-border">
                v1.0 React
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground font-medium hidden sm:block">
              {activeModuleTitle}
            </p>
          </div>
        </div>

        {/* Global Status and Actions */}
        <div className="flex items-center space-x-3">
          {/* Status Badge */}
          <div className="hidden md:flex items-center space-x-2 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-600 dark:text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="font-medium text-[11px]">Motor Físico Operacional</span>
          </div>

          {/* Theme Toggle */}
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleTheme}
            className="h-8 w-8 text-muted-foreground hover:text-foreground"
            title="Alternar tema claro/escuro"
          >
            {isDarkMode ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4" />}
          </Button>

          {/* User info avatar */}
          <div className="flex items-center space-x-2 pl-2 border-l border-border">
            <div className="w-7 h-7 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary text-xs font-bold">
              PE
            </div>
            <div className="hidden lg:block text-left text-xs leading-none">
              <p className="font-semibold text-foreground">Engenheiro Sênior</p>
              <p className="text-[10px] text-muted-foreground">Reservatórios & Produção</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
