"use client"

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard,
    Activity,
    AlertCircle,
    Zap,
    Settings,
    LogOut,
    Menu,
    X,
    Cpu
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";

export default function DashboardLayout({ children, params }: { children: React.ReactNode, params?: any }) {
    const pathname = usePathname();
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    // Determine current domain context for links
    const domain = params?.domain || 'malak';
    const baseUrl = `/c/${domain}`;

    const navItems = [
        { icon: LayoutDashboard, label: "Overview", href: baseUrl },
    ];

    return (
        <div className="min-h-screen bg-background flex overflow-hidden">
            {/* Mobile Sidebar Overlay */}
            {isSidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 lg:hidden"
                    onClick={() => setIsSidebarOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside
                className={`
          fixed lg:static inset-y-0 left-0 z-50 w-64 bg-sidebar border-r border-sidebar-border transform transition-transform duration-200 ease-in-out
          ${isSidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        `}
            >
                <div className="h-full flex flex-col">
                    {/* Logo Area */}
                    <div className="h-16 flex items-center px-6 border-b border-sidebar-border">
                        <Cpu className="h-6 w-6 text-primary mr-2" />
                        <span className="font-sans font-bold text-xl tracking-tight text-sidebar-foreground">
                            AGENTIC<span className="text-primary">.OS</span>
                        </span>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="ml-auto lg:hidden"
                            onClick={() => setIsSidebarOpen(false)}
                        >
                            <X className="h-5 w-5" />
                        </Button>
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
                        {navItems.map((item) => {
                            const isActive = pathname === item.href;
                            return (
                                <Link key={item.href} href={item.href} onClick={() => setIsSidebarOpen(false)}>
                                    <div
                                        className={`
                      flex items-center px-3 py-2.5 rounded-md text-sm font-medium transition-colors cursor-pointer
                      ${isActive
                                                ? "bg-sidebar-accent text-sidebar-accent-foreground border-l-2 border-primary"
                                                : "text-muted-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
                                            }
                    `}
                                    >
                                        <item.icon className={`h-5 w-5 mr-3 ${isActive ? "text-primary" : ""}`} />
                                        {item.label}
                                    </div>
                                </Link>
                            );
                        })}
                    </nav>

                    {/* User Profile */}
                    <div className="p-4 border-t border-sidebar-border">
                        <div className="flex items-center p-2 rounded-md bg-sidebar-accent/30 border border-sidebar-border">
                            <Avatar className="h-9 w-9 border border-primary/30">
                                <AvatarImage src="/images/ai-avatar.jpg" alt="User" />
                                <AvatarFallback className="bg-primary/20 text-primary">MS</AvatarFallback>
                            </Avatar>
                            <div className="ml-3 overflow-hidden">
                                <p className="text-sm font-medium text-sidebar-foreground truncate">Michael Sipes</p>
                                <p className="text-xs text-muted-foreground truncate">Sipes Automation</p>
                            </div>
                            <Button variant="ghost" size="icon" className="ml-auto h-8 w-8 text-muted-foreground hover:text-destructive">
                                <LogOut className="h-4 w-4" />
                            </Button>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                {/* Mobile Header */}
                <header className="lg:hidden h-16 flex items-center px-4 border-b border-border bg-background">
                    <Button variant="ghost" size="icon" onClick={() => setIsSidebarOpen(true)}>
                        <Menu className="h-6 w-6" />
                    </Button>
                    <span className="ml-3 font-display font-bold text-lg">AGENTIC.OS</span>
                </header>

                {/* Page Content */}
                <main className="flex-1 overflow-y-auto p-4 lg:p-8 relative">
                    {/* Background Grid Effect */}
                    <div className="absolute inset-0 pointer-events-none opacity-[0.03]"
                        style={{
                            backgroundImage: `linear-gradient(to right, #1E293B 1px, transparent 1px), linear-gradient(to bottom, #1E293B 1px, transparent 1px)`,
                            backgroundSize: '40px 40px'
                        }}
                    />

                    <div className="relative z-10 max-w-7xl mx-auto">
                        {children}
                    </div>
                </main>
            </div>
        </div>
    );
}
