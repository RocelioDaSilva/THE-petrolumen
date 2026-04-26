"use client";

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, Search, Bell, User } from 'lucide-react';

interface HeaderProps {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

const Header: React.FC<HeaderProps> = ({ sidebarOpen, setSidebarOpen }) => {
  return (
    <header className="bg-background border-b border-border shadow-sm z-10">
      <div className="flex items-center justify-between px-4 md:px-6 py-3">
        {/* Left section: Toggle and Logo/Title */}
        <div className="flex items-center space-x-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-foreground/70 hover:text-foreground"
          >
            {sidebarOpen ? <ChevronLeft className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
            <span className="sr-only">{sidebarOpen ? "Collapse Sidebar" : "Expand Sidebar"}</span>
          </Button>
          <Link href="/" className="flex items-center space-x-2">
            <Image
              src="/placeholder-logo.svg"
              alt="PetroLúmen Logo"
              width={32}
              height={32}
              className="w-8 h-8"
            />
            <span className="text-xl font-semibold text-foreground">
              PetroLúmen
            </span>
          </Link>
        </div>

        {/* Right section: Icons (optional for now) */}
        <div className="flex items-center space-x-2 md:space-x-4">
          <Button variant="ghost" size="icon" className="text-foreground/70 hover:text-foreground">
            <Search className="h-5 w-5" />
            <span className="sr-only">Search</span>
          </Button>
          <Button variant="ghost" size="icon" className="text-foreground/70 hover:text-foreground">
            <Bell className="h-5 w-5" />
            <span className="sr-only">Notifications</span>
          </Button>
          <Button variant="ghost" size="icon" className="text-foreground/70 hover:text-foreground">
            <User className="h-5 w-5" />
            <span className="sr-only">User Profile</span>
          </Button>
        </div>
      </div>
    </header>
  );
};

export default Header;
