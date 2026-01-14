import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Calendar, User, Tag, ExternalLink } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import clsx from 'clsx';

const SummaryPanel = ({ video, onClose }) => {
    return (
        <AnimatePresence>
            {video && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="absolute inset-0 bg-slate-900/20 backdrop-blur-sm z-40 transition-opacity"
                    />

                    {/* Panel */}
                    <motion.div
                        initial={{ x: "100%", opacity: 0.5 }}
                        animate={{ x: 0, opacity: 1 }}
                        exit={{ x: "100%", opacity: 0.5 }}
                        transition={{ type: "spring", damping: 25, stiffness: 200 }}
                        className="absolute top-0 right-0 w-full sm:w-[600px] lg:w-[700px] h-full bg-white/95 backdrop-blur-2xl shadow-2xl border-l border-slate-200 z-50 flex flex-col"
                    >
                        {/* Header */}
                        <div className="flex-none p-6 border-b border-slate-100 bg-white/50">
                            <div className="flex justify-between items-start gap-4 mb-4">
                                <div className="space-y-1">
                                    <div className="flex items-center gap-2 mb-2">
                                        <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 text-xs font-bold uppercase tracking-wider">
                                            {video.channel_title || 'YouTube Channel'}
                                        </span>
                                        {video.published && (
                                            <span className="flex items-center gap-1 text-xs text-slate-500 font-medium">
                                                <Calendar size={12} /> {video.published}
                                            </span>
                                        )}
                                    </div>
                                    <h2 className="text-2xl font-extrabold text-slate-900 leading-tight">
                                        {video.title}
                                    </h2>
                                </div>
                                <button
                                    onClick={onClose}
                                    className="p-2 rounded-full hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors"
                                >
                                    <X size={24} />
                                </button>
                            </div>

                            <div className="flex flex-wrap items-center gap-2 mt-2">
                                {video.tags && video.tags.map((tag, i) => (
                                    <span key={i} className="text-xs font-semibold text-slate-600 bg-slate-100 px-2 py-1 rounded-md">
                                        #{tag}
                                    </span>
                                ))}
                                <a
                                    href={video.link}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="ml-auto inline-flex items-center gap-1 text-xs font-bold text-indigo-600 hover:text-indigo-700 hover:underline"
                                >
                                    Watch Video <ExternalLink size={12} />
                                </a>
                            </div>
                        </div>

                        {/* Content - Scrollable */}
                        <div className="flex-1 overflow-y-auto p-6 scroll-smooth">
                            <div className="prose prose-slate prose-lg max-w-none 
                prose-headings:font-bold prose-headings:text-slate-900 
                prose-h1:text-3xl prose-h2:text-2xl prose-h2:mt-8 prose-h2:mb-4 prose-h2:pb-2 prose-h2:border-b prose-h2:border-slate-100
                prose-h3:text-xl prose-h3:text-indigo-600 prose-h3:mt-6
                prose-p:text-slate-600 prose-p:leading-7 
                prose-strong:text-slate-900 prose-strong:font-bold
                prose-ul:list-disc prose-ul:pl-5 prose-li:text-slate-600 prose-li:marker:text-indigo-400
                prose-blockquote:border-l-4 prose-blockquote:border-indigo-500 prose-blockquote:bg-indigo-50/50 prose-blockquote:px-4 prose-blockquote:py-1 prose-blockquote:rounded-r-lg prose-blockquote:italic
                ">

                                {/* We assume backend serves raw markdown in 'content' field if available, 
                    OR we need to fetch it separately. 
                    Based on 'Dashboard.jsx', we only have 'preview' and 'highlight'. 
                    We need to fetch the full summary when opening. 
                    For now, let's assume 'video.fullSummary' is passed or we fetch it. 
                */}

                                {/* If full content isn't loaded yet, show skeleton or prompt */}
                                {video.isLoadingDetails ? (
                                    <div className="space-y-4 animate-pulse">
                                        <div className="h-4 bg-slate-100 rounded w-3/4"></div>
                                        <div className="h-4 bg-slate-100 rounded w-full"></div>
                                        <div className="h-4 bg-slate-100 rounded w-5/6"></div>
                                        <div className="h-32 bg-slate-100 rounded w-full mt-6"></div>
                                    </div>
                                ) : video.fullContent ? (
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {video.fullContent}
                                    </ReactMarkdown>
                                ) : (
                                    <div className="text-center py-10 text-slate-400">
                                        <p>Detailed summary content not available.</p>
                                    </div>
                                )}
                            </div>

                            {/* Bottom Spacer */}
                            <div className="h-10"></div>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
};

export default SummaryPanel;
