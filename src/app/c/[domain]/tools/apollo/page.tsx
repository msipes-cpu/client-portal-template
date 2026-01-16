"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { AlertCircle, CheckCircle2, Loader2, Sparkles } from "lucide-react"

export default function ApolloEnrichmentPage({ params }: { params: { domain: string } }) {
    const [url, setUrl] = useState("")
    const [target, setTarget] = useState(100)
    const [isLoading, setIsLoading] = useState(false)
    const [url, setUrl] = useState("")
    const [target, setTarget] = useState(100)
    const [isLoading, setIsLoading] = useState(false)
    const [runId, setRunId] = useState<string | null>(null)
    const [progress, setProgress] = useState<{ current: number, total: number } | null>(null)
    const [status, setStatus] = useState<{ type: 'success' | 'error' | null, message: string }>({ type: null, message: '' })

    // Configuration checks
    // Sanitize the URL: Remove surrounding quotes if present, remove trailing slash
    const RAW_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "";
    // Note: We use a local proxy (/api/proxy) so this URL is used by the server-side proxy, 
    // but we sanitize it here just in case we ever switch back or use it for display.

    // Polling Effect
    useEffect(() => {
        if (!runId) return;

        const interval = setInterval(async () => {
            try {
                // Use proxy to fetch run details
                const res = await fetch(`/api/proxy?path=/api/runs/${runId}`);
                if (res.ok) {
                    const data = await res.json();
                    const logs = data.logs || [];

                    // Parse logs for progress
                    // Log format: {"stdout": "[PROGRESS]: 5/100"} or similar inside data.stdout
                    // backend/tasks.py stores it as: data=json.dumps({"stdout": ...})
                    // But backend/main.py parses it back to dict in 'data' field.
                    // So we look for log.data.stdout -> "[PROGRESS]: X/Y"

                    let foundProgress = false;
                    // Read from end to specific to find latest
                    for (let i = logs.length - 1; i >= 0; i--) {
                        const log = logs[i];
                        const stdout = log.data?.stdout || "";
                        if (stdout.includes("[PROGRESS]:")) {
                            const parts = stdout.split("[PROGRESS]:")[1].trim().split("/");
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

                    // Optional: Check if completed
                    if (data.run?.status === "COMPLETED") {
                        setRunId(null); // Stop polling
                        setStatus({ type: 'success', message: `Job Complete! Check your email.` });
                        setProgress(null);
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
            // Ideally we get the user's email from the session/auth context
            // Hardcoding for now based on user context or input if needed
            const userEmail = "msipes@sipesautomation.com"


            // Use local proxy to bypass CORS
            const res = await fetch(`/api/proxy`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    url: url,
                    limit: target,
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
                    message: data.detail || "Failed to start the job. Please try again."
                })
            }
        } catch (error: any) {
            console.error("Submission Error:", error);
            setStatus({ type: 'error', message: `Error: ${error.message || "Is the backend running?"}` })
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
                            <Label htmlFor="apollo-url">Apollo Search URL</Label>
                            <Input
                                id="apollo-url"
                                placeholder="https://app.apollo.io/#/people/search/..."
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                required
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="target">Target # of Verified Leads</Label>
                            <Input
                                id="target"
                                type="number"
                                min={1}
                                max={10000}
                                value={target}
                                onChange={(e) => setTarget(Number(e.target.value))}
                                required
                            />
                            <p className="text-xs text-muted-foreground">
                                Max 10,000 leads per run.
                            </p>
                        </div>

                        {status.message && (
                            <div className={`p-4 rounded-md flex items-center gap-3 ${status.type === 'success' ? 'bg-green-500/10 text-green-600' : 'bg-red-500/10 text-red-600'}`}>
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
        </div>
    )
}
