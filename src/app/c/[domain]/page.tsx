"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Play, Calendar, AlertTriangle, CheckCircle2, Bot, Link as LinkIcon, Lock, Search, Filter, MailCheck, FileSpreadsheet, ArrowRight } from "lucide-react";

export default function ClientDashboard({ params }: { params: { domain: string } }) {
    const [executions, setExecutions] = useState(0);
    const [status, setStatus] = useState<"working" | "error">("working");
    const [nextRun, setNextRun] = useState<string>(new Date().toISOString().split('T')[0]);
    const [apiToken, setApiToken] = useState("");
    const [sheetUrl, setSheetUrl] = useState("");
    const [shareEmail, setShareEmail] = useState("");
    const [reportEmail, setReportEmail] = useState("");
    const [isTesting, setIsTesting] = useState(false);

    // Load saved config on mount
    useEffect(() => {
        const fetchConfig = async () => {
            try {
                // Use hijacked verify endpoint
                const res = await fetch(`/api/instantly/verify?domain=${params.domain}`);
                if (res.ok) {
                    const data = await res.json();
                    if (data.instantlyApiKey) setApiToken(data.instantlyApiKey);
                    if (data.googleSheetUrl) setSheetUrl(data.googleSheetUrl);
                }
            } catch (e) {
                console.error("Failed to load config", e);
            }
        };
        fetchConfig();
    }, [params.domain]);

    // Save config helper
    const saveConfig = async (key?: string, sheet?: string) => {
        try {
            // Use hijacked verify endpoint (PUT)
            await fetch('/api/instantly/verify', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    domain: params.domain,
                    instantlyApiKey: key,
                    googleSheetUrl: sheet
                })
            });
        } catch (e) {
            console.error("Failed to save config", e);
        }
    };

    const handleTestWorkflow = async () => {
        setIsTesting(true);
        try {
            const res = await fetch("/api/instantly/run", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    token: apiToken,
                    sheetUrl: sheetUrl,
                    reportEmail: reportEmail
                })
            });
            const data = await res.json();

            if (data.success) {
                setStatus("working");
                setExecutions(prev => prev + 1);
            } else {
                setStatus("error");
                alert("Workflow Error: " + data.error);
            }
        } catch (e) {
            setStatus("error");
            alert("Network Error");
        } finally {
            setIsTesting(false);
        }
    };

    const [connectionResult, setConnectionResult] = useState<{
        workspace?: string;
        count?: number;
        tags?: {
            Warming: boolean;
            Sending: boolean;
            Benched: boolean;
            Sick: boolean;
        };
        read?: boolean;
        write?: boolean;
        error?: string;
    } | null>(null);
    const [isVerifying, setIsVerifying] = useState(false);

    const handleTestConnection = async () => {
        if (!apiToken) {
            alert("Please enter an API Token first.");
            return;
        }

        setIsVerifying(true);
        setConnectionResult(null);

        try {
            const res = await fetch("/api/instantly/verify", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ token: apiToken })
            });

            const data = await res.json();

            if (data.success) {
                setConnectionResult({
                    workspace: data.workspace_name,
                    count: data.account_count,
                    tags: data.tags,
                    read: data.read_access,
                    write: data.write_access
                });
                // Auto-save API Key on success
                saveConfig(apiToken, undefined);
            } else {
                setConnectionResult({
                    error: data.error || "Verification failed"
                });
            }
        } catch (e) {
            setConnectionResult({ error: "Network error occurred" });
        } finally {
            setIsVerifying(false);
        }
    };

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight mb-2 text-foreground">
                        Mission Control
                        <span className="text-primary ml-2 text-lg font-normal opacity-70 font-mono">
                            / {params.domain}
                        </span>
                    </h1>
                    <p className="text-muted-foreground">
                        Monitor your InboxBench verification agents.
                    </p>
                </div>
                <div className="flex items-center space-x-3 bg-secondary/50 px-4 py-2 rounded-full border border-border">
                    <div className={`status-dot ${status === 'working' ? 'active' : 'error'}`} />
                    <span className="text-sm font-medium uppercase tracking-wider text-muted-foreground">
                        System {status === 'working' ? 'Online' : 'Error'}
                    </span>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Flow Control Card */}
                <div className="lg:col-span-2 space-y-8">
                    <Card className="glass-panel tech-border">
                        <CardHeader>
                            <div className="flex items-start justify-between">
                                <div>
                                    <CardTitle className="text-xl flex items-center">
                                        <Bot className="mr-3 h-6 w-6 text-primary" />
                                        InboxBench Verification
                                    </CardTitle>
                                    <CardDescription className="mt-1">
                                        Automated coding email validation and warmup monitoring.
                                    </CardDescription>
                                </div>
                                <div className="px-3 py-1 rounded-full bg-secondary text-xs uppercase font-mono border border-border text-primary/80">
                                    v2.4.0
                                </div>
                            </div>
                        </CardHeader>
                        <CardContent className="space-y-8">

                            {/* Status Visualizer */}
                            <div className={`
                rounded-xl border p-6 flex flex-col md:flex-row items-center justify-between gap-6
                transition-colors duration-500
                ${status === 'working'
                                    ? 'bg-primary/5 border-primary/20'
                                    : 'bg-destructive/5 border-destructive/20'
                                }
                `}>
                                <div className="flex items-center space-x-5 w-full md:w-auto">
                                    <div className={`
                        p-3 rounded-full shrink-0
                        ${status === 'working' ? 'bg-primary/20' : 'bg-destructive/20'}
                    `}>
                                        {status === 'working' ? (
                                            <CheckCircle2 className={`h-8 w-8 ${status === 'working' ? 'text-primary' : 'text-destructive'}`} />
                                        ) : (
                                            <AlertTriangle className="h-8 w-8 text-destructive" />
                                        )}
                                    </div>
                                    <div>
                                        <h4 className="font-semibold text-lg">
                                            {status === 'working' ? 'Operational' : 'Execution Error'}
                                        </h4>
                                        <p className="text-sm opacity-80 max-w-sm">
                                            {status === 'working'
                                                ? 'Workflow is executing normally. No issues detected in last run.'
                                                : 'Workflow failed during the "Scrape" step. Check logs for details.'}
                                        </p>
                                    </div>
                                </div>
                                <div className="text-right w-full md:w-auto border-t md:border-t-0 border-border/50 pt-4 md:pt-0">
                                    <div className="text-4xl font-mono font-bold tracking-tighter">{executions}</div>
                                    <div className="text-xs uppercase tracking-wider opacity-70">Total Runs</div>
                                </div>
                            </div>

                            {/* Controls */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-3">
                                    <label className="text-sm font-medium text-muted-foreground flex items-center">
                                        <Calendar className="w-4 h-4 mr-2" />
                                        Next Scheduled Run
                                    </label>
                                    <Input
                                        type="date"
                                        value={nextRun}
                                        onChange={(e) => setNextRun(e.target.value)}
                                    />
                                </div>

                                <div className="space-y-3">
                                    <label className="text-sm font-medium text-muted-foreground">Manual Override</label>
                                    <Button
                                        className={`w-full justify-between group ${isTesting ? "opacity-80" : ""}`}
                                        onClick={handleTestWorkflow}
                                        disabled={isTesting}
                                    >
                                        <span className="flex items-center">
                                            <Play className={`w-4 h-4 mr-2 ${isTesting ? "animate-spin" : "group-hover:text-white transition-colors"}`} />
                                            {isTesting ? "Running Workflow..." : "Test Workflow Now"}
                                        </span>
                                        {!isTesting && <span className="font-mono text-xs opacity-50">dev_mode</span>}
                                    </Button>
                                </div>
                            </div>
                        </CardContent>
                        <CardFooter className="bg-secondary/30 border-t border-border/50 flex justify-between items-center text-xs text-muted-foreground">
                            <span>Last updated: just now</span>
                            <span className="font-mono">ID: flow_inboxbench_01</span>
                        </CardFooter>
                    </Card>

                    {/* Visual Workflow Diagram */}
                    <Card className="glass-panel">
                        <CardHeader>
                            <CardTitle className="text-lg">Workflow Visualization</CardTitle>
                            <CardDescription>Live map of the agentic process</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="relative py-4">
                                {/* Connecting Line */}
                                <div className="absolute top-1/2 left-0 w-full h-0.5 bg-border -z-10 hidden md:block" />

                                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                                    {[
                                        { icon: Search, label: "Fetch Data", desc: "Instantly API" },
                                        { icon: Filter, label: "Health Check", desc: "Warmup & Stats" },
                                        { icon: FileSpreadsheet, label: "Update Sheet", desc: "Client Reports" },
                                        { icon: MailCheck, label: "Send Summary", desc: "Daily Email" }
                                    ].map((step, i) => (
                                        <div key={i} className="flex flex-col items-center text-center bg-background md:bg-transparent p-4 md:p-0 rounded-lg border md:border-none border-border">
                                            <div className="w-12 h-12 rounded-full bg-secondary border border-primary/30 flex items-center justify-center mb-3 shadow-[0_0_15px_rgba(16,185,129,0.1)] z-10">
                                                <step.icon className="w-6 h-6 text-primary" />
                                            </div>
                                            <h5 className="font-medium text-sm text-foreground">{step.label}</h5>
                                            <p className="text-xs text-muted-foreground">{step.desc}</p>
                                            {i < 3 && <ArrowRight className="md:hidden mt-3 text-muted-foreground/50" />}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Configuration Side Panel */}
                <div className="space-y-8">
                    {/* Instantly Config */}
                    <Card className="glass-panel border-border/60">
                        <CardHeader>
                            <CardTitle className="text-lg flex items-center">
                                <Lock className="w-4 h-4 mr-2 text-primary" />
                                Credentials
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-muted-foreground">Instantly API Token</label>
                                <Input
                                    type="password"
                                    placeholder="ey..."
                                    value={apiToken}
                                    onChange={(e) => setApiToken(e.target.value)}
                                    className="font-mono text-xs"
                                />
                            </div>
                            <Button
                                variant="outline"
                                className="w-full text-xs"
                                size="sm"
                                onClick={handleTestConnection}
                                disabled={isVerifying}
                            >
                                {isVerifying ? "Verifying..." : "Test Connection"}
                            </Button>

                            {/* Result Display */}
                            {connectionResult && (
                                <div className={`text-xs p-3 rounded-md border ${connectionResult.error ? "bg-destructive/10 border-destructive text-destructive" : "bg-primary/10 border-primary text-white space-y-1"}`}>
                                    {connectionResult.error ? (
                                        <span>{connectionResult.error}</span>
                                    ) : (
                                        <>
                                            <div className="font-semibold flex items-center mb-2">
                                                <CheckCircle2 className="w-3 h-3 mr-1" />
                                                Connection Verified
                                            </div>
                                            <div className="text-[10px] opacity-80 space-y-1">
                                                <p>Workspace: <span className="font-mono text-foreground">{connectionResult.workspace}</span></p>
                                                <p>Accounts: <span className="font-mono text-foreground">{connectionResult.count}</span></p>

                                                {/* Status Tags */}
                                                {connectionResult.tags && (
                                                    <div className="mt-2 pt-2 border-t border-primary/20">
                                                        <p className="font-semibold mb-1 opacity-70">Detecting Tags</p>
                                                        <div className="grid grid-cols-2 gap-x-2 gap-y-1">
                                                            <div className="flex justify-between items-center">
                                                                <span>Warming:</span>
                                                                {connectionResult.tags.Warming ? (
                                                                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                                                                ) : (
                                                                    <span className="text-red-400 font-bold">X</span>
                                                                )}
                                                            </div>
                                                            <div className="flex justify-between items-center">
                                                                <span>Sending:</span>
                                                                {connectionResult.tags.Sending ? (
                                                                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                                                                ) : (
                                                                    <span className="text-red-400 font-bold">X</span>
                                                                )}
                                                            </div>
                                                            <div className="flex justify-between items-center">
                                                                <span>Benched:</span>
                                                                {connectionResult.tags.Benched ? (
                                                                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                                                                ) : (
                                                                    <span className="text-red-400 font-bold">X</span>
                                                                )}
                                                            </div>
                                                            <div className="flex justify-between items-center">
                                                                <span>Sick:</span>
                                                                {connectionResult.tags.Sick ? (
                                                                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                                                                ) : (
                                                                    <span className="text-red-400 font-bold">X</span>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>
                                                )}

                                                <div className="flex gap-2 mt-2 pt-2 border-t border-primary/20">
                                                    <span className={connectionResult.read ? "text-green-400" : "text-red-400"}>R: {connectionResult.read ? "OK" : "FAIL"}</span>
                                                    <span className={connectionResult.write ? "text-green-400" : "text-red-400"}>W: {connectionResult.write ? "OK" : "FAIL"}</span>
                                                </div>
                                            </div>
                                        </>
                                    )}
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Results Config */}
                    <Card className="glass-panel border-border/60">
                        <CardHeader>
                            <CardTitle className="text-lg flex items-center">
                                <LinkIcon className="w-4 h-4 mr-2 text-primary" />
                                Output Configuration
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">

                            {/* Google Sheet Config */}
                            <div className="space-y-2 p-3 bg-secondary/20 rounded-lg border border-border/50">
                                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Google Sheet</label>
                                <div className="space-y-2">
                                    <Input
                                        type="url"
                                        placeholder="https://docs.google.com/..."
                                        value={sheetUrl}
                                        onChange={(e) => setSheetUrl(e.target.value)}
                                        className="text-xs truncate text-muted-foreground bg-background/50"
                                    />
                                    <div className="flex gap-2">
                                        <div className="flex-1">
                                            <Input
                                                type="email"
                                                placeholder="Share with email..."
                                                value={shareEmail}
                                                onChange={(e) => setShareEmail(e.target.value)}
                                                className="text-xs bg-background/50"
                                            />
                                        </div>
                                        <Button
                                            variant="outline"
                                            className="px-3"
                                            title="Create & Share New Sheet"
                                            onClick={async () => {
                                                let msg = "Create a new Google Sheet?";
                                                if (shareEmail) msg += `\nAnd share with ${shareEmail}?`;

                                                const confirmCreate = confirm(msg);
                                                if (!confirmCreate) return;

                                                const btn = document.getElementById('create-sheet-btn');
                                                if (btn) btn.innerText = "...";

                                                try {
                                                    const res = await fetch("/api/sheets/create", {
                                                        method: "POST",
                                                        body: JSON.stringify({
                                                            title: `InboxBench - ${params.domain}`,
                                                            shareEmail: shareEmail
                                                        })
                                                    });
                                                    const data = await res.json();
                                                    if (data.success && data.sheet_url) {
                                                        setSheetUrl(data.sheet_url);
                                                        // Save the new sheet URL
                                                        saveConfig(undefined, data.sheet_url);
                                                        window.open(data.sheet_url, '_blank');
                                                        if (data.shared_with) alert(`Sheet created and shared with ${data.shared_with}`);
                                                    } else {
                                                        alert("Failed to create sheet: " + (data.error || "Unknown error"));
                                                    }
                                                } catch (e) {
                                                    alert("Error creating sheet");
                                                } finally {
                                                    if (btn) btn.innerText = "+";
                                                }
                                            }}
                                        >
                                            <span id="create-sheet-btn" className="text-lg">+</span>
                                        </Button>
                                    </div>
                                    <Button
                                        className="w-full text-xs h-8"
                                        variant="secondary"
                                        onClick={() => {
                                            if (sheetUrl) window.open(sheetUrl, '_blank');
                                            else alert("Please enter a valid URL first.");
                                        }}
                                    >
                                        Open Sheet ↗
                                    </Button>
                                </div>
                            </div>

                            {/* Email Reporting Config */}
                            <div className="space-y-2 p-3 bg-secondary/20 rounded-lg border border-border/50">
                                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Email Reporting</label>
                                <div className="space-y-2">
                                    <Input
                                        type="email"
                                        placeholder="Send report to..."
                                        value={reportEmail}
                                        onChange={(e) => setReportEmail(e.target.value)}
                                        className="text-xs bg-background/50"
                                    />
                                    <p className="text-[10px] text-muted-foreground opacity-70">
                                        * Recipient will get a summary email when workflow runs.
                                    </p>
                                </div>
                            </div>

                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
