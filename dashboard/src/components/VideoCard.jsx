import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Calendar, Tag, ChevronDown, CheckCircle2, AtSign, Loader2 } from 'lucide-react';
import clsx from 'clsx';

const VideoCard = ({ video, onViewSummary }) => {
    const [isRead, setIsRead] = useState(video.is_read || false);
    const [isLoading, setIsLoading] = useState(false);
    const [isThreadsLoading, setIsThreadsLoading] = useState(false);
    const [threadsStatus, setThreadsStatus] = useState('idle'); // 'idle' | 'success' | 'error'

    // Gradient generator for tags
    const getTagStyle = (index) => {
        const styles = [
            'bg-indigo-50 text-indigo-700 border-indigo-200',
            'bg-violet-50 text-violet-700 border-violet-200',
            'bg-emerald-50 text-emerald-700 border-emerald-200',
            'bg-rose-50 text-rose-700 border-rose-200'
        ];
        return styles[index % styles.length];
    };

    const handleToggleRead = async (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsLoading(true);
        try {
            const response = await fetch(`http://localhost:8000/api/videos/${video.id}/toggle_read`, {
                method: 'POST'
            });
            if (response.ok) {
                setIsRead(!isRead);
            }
        } catch (error) {
            console.error("Failed to toggle read status", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleThreadsSubmit = async (e) => {
        e.preventDefault();
        e.stopPropagation();

        const webhookUrl = import.meta.env.VITE_THREADS_WEBHOOK_URL;
        if (!webhookUrl || webhookUrl === 'your_webhook_url_here') {
            alert("Please configure VITE_THREADS_WEBHOOK_URL in your .env file");
            return;
        }

        setIsThreadsLoading(true);
        setThreadsStatus('idle');

        try {
            // Fetch full content if not already available
            let finalSummary = video.fullContent || video.highlight || video.preview || "No summary available.";

            try {
                const summaryRes = await fetch(`/api/summary/${video.id}`);
                if (summaryRes.ok) {
                    const summaryData = await summaryRes.json();
                    if (summaryData && summaryData.content) {
                        finalSummary = summaryData.content;
                    }
                }
            } catch (err) {
                console.warn("Could not fetch full summary, falling back to preview", err);
            }

            const response = await fetch(webhookUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: video.title,
                    link: video.link,
                    summary: finalSummary,
                    channel: video.channel_title,
                    timestamp: new Date().toISOString()
                })
            });

            if (response.ok) {
                setThreadsStatus('success');
                setTimeout(() => setThreadsStatus('idle'), 3000);
            } else {
                setThreadsStatus('error');
            }
        } catch (error) {
            console.error("Failed to send to Threads Webhook", error);
            setThreadsStatus('error');
        } finally {
            setIsThreadsLoading(false);
        }
    };

    return (
        <motion.div
            layout
            transition={{ layout: { duration: 0.3 } }}
            className={clsx(
                "group relative bg-white rounded-xl border shadow-soft transition-all duration-300 overflow-hidden",
                isRead
                    ? "border-slate-100 opacity-60 grayscale-[0.5] hover:opacity-100 hover:grayscale-0 hover:-translate-y-1"
                    : "border-slate-100 hover:shadow-soft-hover hover:-translate-y-1"
            )}
        >
            <div className="p-5">
                {/* Header Section */}
                <div className="flex justify-between items-start gap-4 mb-3">
                    <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                            <span className="inline-flex items-center gap-1 text-[10px] font-bold tracking-wider text-slate-500 uppercase bg-slate-100 px-2 py-0.5 rounded-full">
                                {video.channel_title || 'YouTube'}
                            </span>
                            {video.has_summary && (
                                <span className="inline-flex items-center gap-1 text-[10px] font-bold tracking-wider text-emerald-600 uppercase bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100">
                                    <CheckCircle2 size={10} strokeWidth={3} />
                                    Summarized
                                </span>
                            )}
                        </div>
                        <h3 className={clsx(
                            "text-lg font-bold leading-tight transition-colors line-clamp-2",
                            isRead ? "text-slate-500 decoration-slate-300" : "text-slate-900 group-hover:text-indigo-600"
                        )}>
                            <a href={video.link} target="_blank" rel="noopener noreferrer" className="hover:underline decoration-indigo-200 underline-offset-2">
                                {video.title}
                            </a>
                        </h3>
                    </div>

                    <div className="flex gap-2 shrink-0">
                        {/* Done Button */}
                        <button
                            onClick={handleToggleRead}
                            disabled={isLoading}
                            title={isRead ? "Mark as Unread" : "Mark as Done"}
                            className={clsx(
                                "w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 shadow-sm border",
                                isRead
                                    ? "bg-emerald-100 text-emerald-600 border-emerald-200"
                                    : "bg-white text-slate-400 border-slate-100 hover:bg-emerald-50 hover:text-emerald-600 hover:border-emerald-200"
                            )}
                        >
                            <CheckCircle2 size={18} className={clsx("transition-transform duration-300", isLoading && "animate-pulse")} />
                        </button>

                        {/* Threads Button */}
                        <button
                            onClick={handleThreadsSubmit}
                            disabled={isThreadsLoading}
                            title="Post to Threads"
                            className={clsx(
                                "w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 shadow-sm border",
                                threadsStatus === 'success'
                                    ? "bg-indigo-100 text-indigo-600 border-indigo-200"
                                    : threadsStatus === 'error'
                                        ? "bg-rose-100 text-rose-600 border-rose-200"
                                        : "bg-slate-50 text-slate-500 border-slate-200 hover:bg-indigo-50 hover:text-indigo-600 hover:border-indigo-200"
                            )}
                        >
                            {isThreadsLoading ? (
                                <Loader2 size={18} className="animate-spin" />
                            ) : (
                                <AtSign size={18} className={clsx("transition-transform duration-300", threadsStatus === 'success' && "scale-110")} />
                            )}
                        </button>
                    </div>
                </div>

                {/* Video Meta */}
                <div className="flex items-center gap-4 text-xs text-slate-500 font-medium mb-4">
                    <span className="flex items-center gap-1.5">
                        <Calendar size={14} className="text-slate-400" />
                        {video.published || 'Recently'}
                    </span>
                </div>

                {/* Highlight/Preview */}
                <div className="relative mb-4">
                    <div className="text-slate-600 text-sm leading-relaxed line-clamp-3">
                        {video.highlight || video.preview || "No summary available."}
                    </div>
                </div>

                {/* Tags */}
                <div className="flex flex-wrap gap-2 mb-4">
                    {video.tags && video.tags.slice(0, 3).map((tag, i) => (
                        <span key={i} className={clsx("text-xs font-semibold px-2.5 py-1 rounded-md border", getTagStyle(i))}>
                            #{tag}
                        </span>
                    ))}
                </div>

                {/* View Summary Action */}
                <button
                    onClick={onViewSummary}
                    className="w-full flex items-center justify-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-indigo-600 transition-colors py-2 border-t border-slate-50 mt-2 group/btn"
                >
                    View Full Summary
                    <ChevronDown size={14} className="group-hover/btn:-rotate-90 transition-transform duration-200" />
                </button>
            </div>

            {/* Decorative Bottom Line */}
            <div className={clsx(
                "h-1 w-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 transition-opacity duration-300",
                isRead ? "opacity-0" : "opacity-0 group-hover:opacity-100"
            )}></div>
        </motion.div>
    );
};

export default VideoCard;
