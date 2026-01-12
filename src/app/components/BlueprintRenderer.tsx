"use client";

import React, { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import mermaid from "mermaid";
import clsx from "clsx";

interface BlueprintRendererProps {
    content: string;
}

export function BlueprintRenderer({ content }: BlueprintRendererProps) {
    const mermaidRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        mermaid.initialize({
            startOnLoad: true,
            theme: "dark",
            securityLevel: "loose",
        });
        mermaid.contentLoaded();
    }, [content]);

    return (
        <div className="prose prose-invert prose-indigo max-w-none">
            <ReactMarkdown
                components={{
                    // Custom Code Block Renderer for Mermaid
                    code(props) {
                        const { children, className, node, ...rest } = props;
                        const match = /language-(\w+)/.exec(className || "");
                        const language = match ? match[1] : "";

                        if (language === "mermaid") {
                            return (
                                <div className="mermaid bg-slate-900/50 p-4 rounded-xl border border-white/5 my-6 overflow-x-auto">
                                    {children}
                                </div>
                            );
                        }

                        return (
                            <code className={clsx("bg-slate-800 rounded px-1 py-0.5", className)} {...rest}>
                                {children}
                            </code>
                        );
                    },
                    // Custom Pre Block
                    pre(props) {
                        return <pre className="bg-slate-900 p-4 rounded-xl overflow-x-auto border border-white/10" {...props} />;
                    }
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
}
