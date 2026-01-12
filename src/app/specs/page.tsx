import React from "react";
import { BlueprintRenderer } from "../components/BlueprintRenderer";
import fs from "fs";
import path from "path";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

async function getBlueprintContent() {
    // In production, you might fetch this from a URL or CMS.
    // For the template, we read from the public folder or root.
    const filePath = path.join(process.cwd(), "public", "blueprint.md");
    try {
        const fileContent = fs.readFileSync(filePath, "utf8");
        return fileContent;
    } catch (error) {
        return "# Blueprint Not Found\nPlease upload a `blueprint.md` file to the public folder.";
    }
}

export default async function SpecsPage() {
    const content = await getBlueprintContent();

    return (
        <main className="min-h-screen p-8 lg:p-20 bg-slate-950">
            <div className="max-w-4xl mx-auto">
                <Link href="/" className="inline-flex items-center text-gray-400 hover:text-white mb-8 transition-colors">
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Back to Dashboard
                </Link>

                <div className="bg-slate-900/30 border border-white/10 p-8 rounded-3xl backdrop-blur-sm">
                    <BlueprintRenderer content={content} />
                </div>
            </div>
        </main>
    );
}
