"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { AlertCircle, CheckCircle2, Loader2, Sparkles } from "lucide-react"

export default function ApolloEnrichmentPage({ params }: { params: { domain: string } }) {
    const [url, setUrl] = useState("")
    const [target, setTarget] = useState(100)
    const [isLoading, setIsLoading] = useState(false)
    const [status, setStatus] = useState<{ type: 'success' | 'error' | null, message: string }>({ type: null, message: '' })

    // Configuration checks
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsLoading(true)
        setStatus({ type: null, message: '' })

        if (!BACKEND_URL) {
            setStatus({ type: 'error', message: 'Backend URL is not configured. Please set NEXT_PUBLIC_BACKEND_URL.' })
            setIsLoading(false)
            return
        }

        try {
            // Ideally we get the user's email from the session/auth context
            // Hardcoding for now based on user context or input if needed
            const userEmail = "msipes@sipesautomation.com"

            const res = await fetch(`${BACKEND_URL}/api/leads/process-url`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    url: url,
                    limit: target, // Backend expects 'limit'
                    email: userEmail
                })
            })

            const data = await res.json()

            if (res.ok) {
                setStatus({
                    type: 'success',
                    message: `Enrichment job started (Run ID: ${data.run_id})! You will receive an email with the results at ${userEmail} shortly.`
                })
                setUrl("")
            } else {
                setStatus({
                    type: 'error',
                    message: data.detail || "Failed to start the job. Please try again."
                })
            }
        } catch (error) {
            setStatus({ type: 'error', message: "An unexpected error occurred. Is the backend running?" })
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

                        <Button type="submit" className="w-full" disabled={isLoading}>
                            {isLoading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Starting Workflow...
                                </>
                            ) : (
                                "Start Enrichment"
                            )}
                        </Button>
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
