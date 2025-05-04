"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Camera, BarChart2, Settings, CheckCircle, Clipboard, BarChart } from "lucide-react"
import { cn } from "@/lib/utils"

const navItems = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: Camera,
  },
  {
    name: "Performance",
    href: "/performance",
    icon: BarChart2,
  },
  {
    name: "Accuracy",
    href: "/accuracy",
    icon: CheckCircle,
  },
  {
    name: "Tasks",
    href: "/tasks",
    icon: Clipboard,
  },
  {
    name: "Statistics",
    href: "/statistics",
    icon: BarChart,
  },
  {
    name: "Settings",
    href: "/settings",
    icon: Settings,
  },
]

export function Header() {
  const pathname = usePathname()

  return (
    <header className="w-full border-b bg-background">
      <div className="container mx-auto">
        <div className="py-4">
          <h1 className="text-2xl font-bold">Camera Dashboard</h1>
        </div>
        <nav className="flex space-x-1 pb-2">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center rounded-md px-3 py-2 text-sm font-medium",
                pathname === item.href ? "bg-primary text-primary-foreground" : "hover:bg-muted",
              )}
            >
              <item.icon className="mr-2 h-4 w-4" />
              {item.name}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  )
}
