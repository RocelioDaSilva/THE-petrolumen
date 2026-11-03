import {
  BarChart3,
  Database,
  Gauge,
  Home,
  Settings,
  TrendingUp,
  Zap,
  Brain,
  TestTube,
  DollarSign,
  Eye,
  Workflow,
} from "lucide-react"
import Link from "next/link"

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
} from "@/components/ui/sidebar"

const menuItems = [
  {
    title: "Dashboard",
    url: "/",
    icon: Home,
  },
  {
    title: "Reservoir Simulation",
    url: "/simulation",
    icon: Database,
  },
  {
    title: "Production Analysis",
    url: "/production",
    icon: TrendingUp,
  },
  {
    title: "Optimization & History Matching",
    url: "/optimization",
    icon: Settings,
  },
  {
    title: "Static/Dynamic Modeling",
    url: "/modeling",
    icon: BarChart3,
  },
  {
    title: "Uncertainty & Sensitivity",
    url: "/uncertainty",
    icon: Gauge,
  },
  {
    title: "Well Testing",
    url: "/well-testing",
    icon: TestTube,
  },
  {
    title: "Economic Analysis",
    url: "/economics",
    icon: DollarSign,
  },
  {
    title: "Visualization",
    url: "/visualization",
    icon: Eye,
  },
  {
    title: "Advanced Analytics & AI",
    url: "/analytics",
    icon: Brain,
  },
  {
    title: "Integration & Automation",
    url: "/integration",
    icon: Workflow,
  },
]

export function AppSidebar() {
  return (
    <Sidebar>
      <SidebarHeader className="border-b p-4">
        <div className="flex items-center gap-2">
          <Zap className="h-6 w-6 text-blue-600" />
          <span className="font-semibold text-lg">PetroEng Platform</span>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {menuItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <Link href={item.url}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  )
}
