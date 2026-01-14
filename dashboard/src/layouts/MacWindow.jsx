import React from 'react';
import { motion } from 'framer-motion';

const MacWindow = ({ children }) => {
    return (
        <div className="min-h-screen flex items-center justify-center p-4 sm:p-8 relative overflow-hidden bg-slate-50">
            {/* Ambient Background Blobs */}
            <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob"></div>
            <div className="absolute top-0 right-1/4 w-96 h-96 bg-indigo-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000"></div>
            <div className="absolute -bottom-8 left-1/3 w-96 h-96 bg-pink-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-4000"></div>

            {/* Main Window Container */}
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className="relative z-10 w-full max-w-7xl h-[85vh] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-slate-200/60 backdrop-blur-xl"
            >
                {/* Window Header */}
                <div className="h-12 bg-slate-100/80 border-b border-slate-200 flex items-center px-4 shrink-0 backdrop-blur-sm">
                    <div className="flex space-x-2">
                        <div className="w-3 h-3 rounded-full bg-red-500 border border-red-600/20 hover:bg-red-600 transition-colors"></div>
                        <div className="w-3 h-3 rounded-full bg-yellow-500 border border-yellow-600/20 hover:bg-yellow-600 transition-colors"></div>
                        <div className="w-3 h-3 rounded-full bg-green-500 border border-green-600/20 hover:bg-green-600 transition-colors"></div>
                    </div>
                    <div className="flex-1 text-center">
                        <span className="text-xs font-medium text-slate-500 flex items-center justify-center gap-1.5">
                            <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span>
                            AI Summarizer Dashboard
                        </span>
                    </div>
                    <div className="w-14"></div> {/* Spacer for center alignment */}
                </div>

                {/* Content Area */}
                <div className="flex-1 overflow-auto bg-slate-50/50 p-6 sm:p-8">
                    {children}
                </div>
            </motion.div>
        </div>
    );
};

export default MacWindow;
