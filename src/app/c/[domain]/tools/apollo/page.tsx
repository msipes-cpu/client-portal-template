"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Loader2, CheckCircle2, AlertCircle, ArrowUpDown, Download } from "lucide-react"

export default function ApolloEnrichmentPage({ params }: { params: { domain: string } }) {
    const [url, setUrl] = useState("")
    const [target, setTarget] = useState(100)
    const [isLoading, setIsLoading] = useState(false)
    const [runId, setRunId] = useState<string | null>(null)
    const [progress, setProgress] = useState<{ current: number, total: number } | null>(null)
    const [status, setStatus] = useState<{ type: 'success' | 'error' | null, message: string }>({ type: null, message: '' })
    const [recentRuns, setRecentRuns] = useState<any[]>([])
    const [loadingSheet, setLoadingSheet] = useState<string | null>(null)

    // Configuration checks
    // Sanitize the URL: Remove surrounding quotes if present, remove trailing slash
    const RAW_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "";
    // Note: We use a local proxy (/api/proxy) so this URL is used by the server-side proxy, 
    // but we sanitize it here just in case we ever switch back or use it for display.

    // Ideally we get the user's email from the session/auth context
    // Hardcoding for now based on user context or input if needed
    const userEmail = "msipes@sipesautomation.com"

    // Fetch Recent Runs Effect
    useEffect(() => {
        const fetchRuns = async () => {
            try {
                // Fetch from admin runs endpoint via proxy to get metadata
                const res = await fetch(`/api/proxy?path=/api/admin/runs`);
                if (res.ok) {
                    const data = await res.json();
                    if (data.runs) {
                        // Filter by user email
                        const myRuns = data.runs.filter((r: any) =>
                            r.meta?.email === userEmail ||
                            // Fallback if args parse failed but we want to show something?
                            // For now stick to strict email match
                            false
                        );
                        setRecentRuns(myRuns);
                    }
                }
            } catch (e) {
                console.error("Error fetching recent runs:", e);
            }
        };

        fetchRuns();
        // Refresh every 30s
        const interval = setInterval(fetchRuns, 30000);
        return () => clearInterval(interval);
    }, []);

    const downloadCSV = async (runId: string) => {
        setLoadingSheet(runId);
        try {
            // Fetch leads from backend
            const res = await fetch(`/api/proxy?path=/api/runs/${runId}/leads`);
            if (res.ok) {
                const data = await res.json();
                const leads = data.leads || [];

                if (leads.length === 0) {
                    alert("No leads found for this run yet.");
                    setLoadingSheet(null);
                    return;
                }

                // Convert to CSV
                // 1. Get headers
                const headers = Object.keys(leads[0]).filter(k => k !== 'raw_data' && k !== 'id' && k !== 'run_id');

                // 2. Build CSV string
                const csvRows = [
                    headers.join(','), // Header row
                    ...leads.map((lead: any) => {
                        return headers.map(header => {
                            let val = lead[header] || "";
                            // Escape quotes and wrap in quotes
                            const escaped = String(val).replace(/"/g, '""');
                            return `"${escaped}"`;
                        }).join(',');
                    })
                ];

                const csvString = csvRows.join('\n');

                // 3. Trigger Download
                const blob = new Blob([csvString], { type: 'text/csv' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `leads_${runId}.csv`;
                a.click();
                window.URL.revokeObjectURL(url);

            } else {
                alert("Failed to fetch leads.");
            }
        } catch (e) {
            console.error("Error downloading CSV:", e);
            alert("Error downloading CSV.");
        } finally {
            setLoadingSheet(null);
        }
    };

    // Polling Effect (kept separate for clarity)
    useEffect(() => {
        if (!runId) return;

        const interval = setInterval(async () => {
            try {
                // Use proxy to fetch run details
                const res = await fetch(`/api/proxy?path=/api/runs/${runId}`);
                if (res.ok) {
                    const data = await res.json();
                    const logs = data.logs || [];

                    console.log("Polling Logs:", logs.length, "entries"); // Debug

                    // Parse logs for progress
                    let foundProgress = false;
                    // Read from end to specific to find latest
                    for (let i = logs.length - 1; i >= 0; i--) {
                        const log = logs[i];
                        const stdout = log.data?.stdout || "";

                        // Robust parsing for [PROGRESS]: 5/100
                        if (stdout.includes("[PROGRESS]:")) {
                            const raw = stdout.split("[PROGRESS]:")[1].trim();
                            // console.log("Found progress line:", raw); // Debug
                            const parts = raw.split("/");
                            if (parts.length === 2) {
                                setProgress({
                                    current: parseInt(parts[0]),
                                    total: parseInt(parts[1])
                                });
                                foundProgress = true;
                                break;
                            }
                        }
                    }

                    if (data.run?.status === "COMPLETED") {
                        setRunId(null);
                        setStatus({ type: 'success', message: `Job Complete! Check your email.` });
                        // Keep progress at 100% or whatever it was
                        // setProgress(null); // Look at this? Removing this keeps the bar visible.

                        // Refresh runs list immediately
                        const fetchRuns = async () => {
                            try {
                                const res = await fetch(`/api/proxy?path=/api/admin/runs`);
                                if (res.ok) {
                                    const data = await res.json();
                                    if (data.runs) {
                                        const myRuns = data.runs.filter((r: any) =>
                                            r.meta?.email === userEmail
                                        );
                                        setRecentRuns(myRuns);
                                    }
                                }
                            } catch (e) { }
                        };
                        fetchRuns();
                    }
                }
            } catch (e) {
                console.error("Polling error", e);
            }
        }, 2000);

        return () => clearInterval(interval);
    }, [runId]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsLoading(true)
        setStatus({ type: null, message: '' })

        if (!RAW_URL) {
            setStatus({ type: 'error', message: 'Backend URL is not configured. Please set NEXT_PUBLIC_BACKEND_URL.' })
            setIsLoading(false)
            return
        }

        try {
            // Use local proxy to bypass CORS
            const res = await fetch(`/api/proxy`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    url: url,
                    limit: parseInt(target.toString()),
                    email: userEmail
                })
            })

            const data = await res.json()

            if (res.ok) {
                setRunId(data.run_id); // Start polling
                setStatus({
                    type: 'success',
                    message: `Enrichment job started! You will receive an email shortly.`
                })
                setUrl("")
            } else {
                setStatus({
                    type: 'error',
                    message: data.message || "Failed to start the job. Please try again."
                })
            }
        } catch (error: unknown) {
            console.error("Submission Error:", error);
            setStatus({ type: 'error', message: `Error: ${(error as Error).message || "Is the backend running?"}` })
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center space-x-4">
                <div className="p-3 bg-primary/10 rounded-full">
                    <Sparkles className="h-8 w-8 text-primary" />
                </div>
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Lead Enrichment</h1>
                    <p className="text-muted-foreground">
                        Turn Apollo searches into verified, enriched lead lists automatically.
                    </p>
                </div>
            </div>

            <Card className="max-w-2xl">
                <CardHeader>
                    <CardTitle>New Enrichment Job</CardTitle>
                    <CardDescription>
                        Paste an Apollo Search URL below. We will scrape, enrich (Blitz -&gt; AnyMail), and verify (MillionVerifier) the contacts.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="url">Apollo Search URL</Label>
                            <Input
                                id="url"
                                placeholder="https://app.apollo.io/#/people/search/..."
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                required
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="target">Target # of Verified Leads</Label>
                            <div className="relative">
                                <Input
                                    id="target"
                                    type="number"
                                    min={1}
                                    max={10000}
                                    value={target}
                                    onChange={(e) => setTarget(Number(e.target.value))}
                                    required
                                    className="pr-12"
                                />
                                <div className="absolute inset-y-0 right-3 flex items-center pointer-events-none">
                                    <ArrowUpDown className="h-4 w-4 text-muted-foreground" />
                                </div>
                            </div>
                            <p className="text-xs text-muted-foreground">
                                Max 10,000 leads per run.
                            </p>
                        </div>

                        {status.message && (
                            <div className={`p-4 rounded-md flex items-center gap-3 ${status.type === 'success' ? 'bg-green-500/15 text-green-500' : 'bg-red-500/15 text-red-500'}`}>
                                {status.type === 'success' ? <CheckCircle2 className="h-5 w-5" /> : <AlertCircle className="h-5 w-5" />}
                                <p className="text-sm font-medium">{status.message}</p>
                            </div>
                        )}

                        <Button type="submit" className="w-full" disabled={isLoading || !!runId}>
                            {isLoading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Starting Workflow...
                                </>
                            ) : runId ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Processing Leads...
                                </>
                            ) : (
                                "Start Enrichment"
                            )}
                        </Button>

                        {progress && (
                            <div className="space-y-1 pt-2">
                                <div className="flex justify-between text-xs text-muted-foreground">
                                    <span>Processing...</span>
                                    <span>{progress.current} / {progress.total}</span>
                                </div>
                                <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-primary transition-all duration-500 ease-in-out"
                                        style={{ width: `${(progress.current / progress.total) * 100}%` }}
                                    />
                                </div>
                            </div>
                        )}
                    </form>
                </CardContent>
                <CardFooter className="bg-muted/50 text-xs text-muted-foreground">
                    <p>
                        This process typically takes 1-5 minutes depending on the target size. You can close this page after starting.
                    </p>
                </CardFooter>
            </Card>

            {/* Recent Runs Section */}
            {recentRuns.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg">Recent Jobs</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {recentRuns.map((run) => (
                                <div key={run.run_id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border rounded-lg bg-muted/20 gap-4">
                                    <div className="space-y-1">
                                        <div className="flex items-center gap-2">
                                            <span className={`h-2 w-2 rounded-full ${run.status === 'COMPLETED' ? 'bg-green-500' :
                                                run.status === 'FAILED' || run.status === 'ERROR' ? 'bg-red-500' :
                                                    'bg-blue-500 animate-pulse'
                                                }`} />
                                            <span className="font-medium text-sm">
                                                {new Date(run.start_time.endsWith('Z') ? run.start_time : run.start_time + 'Z').toLocaleString()}
                                            </span>
                                            <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded uppercase">
                                                {run.status}
                                            </span>
                                        </div>
                                        <p className="text-xs text-muted-foreground truncate max-w-[300px]" title={run.meta?.url}>
                                            {run.meta?.url}
                                        </p>
                                        <div className="text-xs text-muted-foreground">
                                            Target: {run.meta?.limit || 'Unknown'} Leads
                                        </div>
                                    </div>

                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => downloadCSV(run.run_id)}
                                        disabled={loadingSheet === run.run_id || run.status !== 'COMPLETED'}
                                    >
                                        {loadingSheet === run.run_id ? (
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                        ) : (
                                            <div className="flex items-center gap-2">
                                                <Download className="h-4 w-4" />
                                                <span>Download CSV</span>
                                            </div>
                                        )}
                                    </Button>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}
