"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowRight, Mail, Zap, LayoutDashboard } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

export default function AutomationsPage() {
    const params = useParams();
    const domain = params?.domain as string || 'malak';
    const baseUrl = `/c/${domain}`;

    const automations = [
        {
            title: "InboxBench Verification",
            description: "Automated coding email validation and warmup monitoring.",
            icon: LayoutDashboard,
            href: baseUrl, // Points to Overview
            status: "Active",
            restricted: false,
        },
        {
            title: "Lead Enrichment",
            description: "Enrich Apollo leads with verified emails using Waterfall methodology.",
            icon: Zap,
            href: `${baseUrl}/tools/apollo`,
            status: "Beta",
            restricted: true, // Only for 'sa'
        }
    ];

    return (
        <div className="space-y-8">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Automations</h2>
                <p className="text-muted-foreground mt-2">
                    Manage and run your intelligent automation agents.
                </p>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {automations.map((tool) => {
                    // Hide restricted tools if not on 'sa' domain
                    if (tool.restricted && domain !== 'sa') return null;

                    return (
                        <Card key={tool.title} className="hover:shadow-md transition-all border-border/50 bg-card/50 backdrop-blur-sm">
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-lg font-medium">
                                    {tool.title}
                                </CardTitle>
                                <tool.icon className="h-5 w-5 text-primary" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-sm text-muted-foreground mb-4 min-h-[40px]">
                                    {tool.description}
                                </div>
                                <div className="flex items-center justify-between">
                                    <Badge variant={tool.status === 'Active' ? 'default' : 'secondary'} className="bg-primary/10 text-primary hover:bg-primary/20 border-0">
                                        {tool.status}
                                    </Badge>
                                    <Link href={tool.href}>
                                        <Button size="sm" variant="ghost" className="gap-2 group">
                                            Open Tool
                                            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                                        </Button>
                                    </Link>
                                </div>
                            </CardContent>
                        </Card>
                    );
                })}
            </div>
        </div>
    );
}
