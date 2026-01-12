"use client";

import React from "react";
import { motion } from "framer-motion";
import { Activity, CheckCircle, Clock } from "lucide-react";

interface StatusCardProps {
    status: string;
    progress: number;
    phase: string;
    milestone: string;
}

export function StatusCard({ status, progress, phase, milestone }: StatusCardProps) {
    return (
        <div className="glass-panel p-6 rounded-2xl w-full max-w-2xl mx-auto mt-10">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Project Status</h2>
                    <div className="flex items-center gap-2 mt-1">
                        <span className="relative flex h-3 w-3">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                        </span>
                        <span className="text-xl font-bold text-white capitalize">{status}</span>
                    </div>
                </div>
                <div className="text-right">
                    <h3 className="text-sm text-gray-400">Current Phase</h3>
                    <p className="text-indigo-300 font-medium">{phase}</p>
                </div>
            </div>

            {/* Progress Bar */}
            <div className="relative h-4 bg-gray-800 rounded-full overflow-hidden mb-4">
                <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 1.5, ease: "easeInOut" }}
                    className="absolute h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                />
            </div>
            <div className="flex justify-between text-xs text-gray-400">
                <span>Start</span>
                <span>{progress}% Complete</span>
                <span>Launch</span>
            </div>

            {/* Next Milestone */}
            <div className="mt-6 flex items-center gap-3 bg-white/5 p-4 rounded-xl border border-white/5">
                <Clock className="w-5 h-5 text-indigo-400" />
                <div>
                    <p className="text-xs text-gray-400">Up Next</p>
                    <p className="text-sm font-medium text-white">{milestone}</p>
                </div>
            </div>
        </div>
    );
}
