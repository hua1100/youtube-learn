import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Calendar, User, Tag, ExternalLink, FilePlus, Save } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import clsx from 'clsx';

const SummaryPanel = ({ video, onClose }) => {
    const [selection, setSelection] = useState(null);
    const [note, setNote] = useState('');
    const contentRef = useRef(null);

    // Initial check for selection clearing when clicking outside
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (selection && !e.target.closest('.selection-popup')) {
                setSelection(null);
                // Clear highlights if we click away without saving
                CSS.highlights?.delete('obsidian-selection');
            }
        };

        const handleMouseUpGlobal = (e) => {
            // 1. Get Selection
            const sel = window.getSelection();

            // 2. Validate Selection presence and non-empty
            if (!sel || sel.isCollapsed || sel.toString().trim().length === 0) {
                return;
            }

            // 3. Validate Context (Is it inside our contentRef?)
            if (contentRef.current && !contentRef.current.contains(sel.anchorNode)) {
                return;
            }

            // 4. If we are clicking inside the popup, do not reset/move it
            if (e.target.closest('.selection-popup')) {
                return;
            }

            // 5. Calculate position
            const range = sel.getRangeAt(0);
            const rect = range.getBoundingClientRect();

            // Check if rect is visible/valid
            if (rect.width === 0 || rect.height === 0) return;

            // --- Highlight API Logic ---
            if (CSS.highlights) {
                const highlight = new Highlight(range);
                CSS.highlights.set('obsidian-selection', highlight);
            }

            setSelection({
                text: sel.toString().trim(),
                x: rect.left + rect.width / 2,
                y: rect.bottom,
            });
            setNote('');
        };

        document.addEventListener('mousedown', handleClickOutside);
        document.addEventListener('pointerup', handleMouseUpGlobal);

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
            document.removeEventListener('pointerup', handleMouseUpGlobal);
        };
    }, [selection]);



    const handleAddToObsidian = () => {
        if (!selection) return;

        // Sanitize video title for filename (remove illegal chars for files)
        const safeTitle = (video.title || 'Untitled')
            .replace(/[\\/:*?"<>|]/g, '-') // Replace system reserved chars
            .replace(/\s+/g, ' ')           // Collapse whitespace
            .trim();

        // Add original link for reference
        const content = `> ${selection.text}\n\n${note}\n\n[Original Video](${video.link})`;

        // Use title + short date to ensure uniqueness but readability
        const dateStr = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
        const filename = `${safeTitle} - ${dateStr}`;

        // Construct Obsidian URI
        const uri = `obsidian://new?name=${encodeURIComponent(filename)}&content=${encodeURIComponent(content)}`;

        window.location.href = uri;

        // Clean up
        setSelection(null);
        window.getSelection().removeAllRanges();
        CSS.highlights?.delete('obsidian-selection');
    };
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
                        <div
                            ref={contentRef}
                            className={`flex-1 p-6 scroll-smooth relative ${selection ? 'overflow-hidden' : 'overflow-y-auto'}`}
                        >
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

                    {/* Text Selection Popup */}
                    {selection && (
                        <Popup
                            selection={selection}
                            onSave={handleAddToObsidian}
                            note={note}
                            setNote={setNote}
                        />
                    )}
                </>
            )}
        </AnimatePresence>
    );
};

// Sub-component for smart positioning
const Popup = ({ selection, onSave, note, setNote }) => {
    const popupRef = useRef(null);
    const [style, setStyle] = useState({
        opacity: 0, // Hidden until positioned
        left: selection.x,
        top: selection.y
    });

    React.useEffect(() => {
        if (!popupRef.current) return;

        const popupRect = popupRef.current.getBoundingClientRect();
        const viewportHeight = window.innerHeight;
        const gap = 8; // Closer gap as requested

        let top = selection.y + gap;

        // Check if popup goes off-screen bottom
        if (top + popupRect.height > viewportHeight - 20) {
            // Flip to top: rect.top - popupHeight - gap
            // We need rect.top, but 'selection' only has 'y' (which is bottom) and 'x'
            // We need to pass the height of the selection or original top to calculate 'above' perfectly.
            // Let's approximate or update 'selection' state to include 'top'.

            // For now, let's just shift it up by popupHeight + gap + line height (approx 24px)
            // Better: Update parent to pass full rect info.
            // But to fix quickly: just shift up by popupHeight + gap + 30px
            top = selection.y - popupRect.height - gap - 24;
        }

        setStyle({
            top: `${top}px`,
            left: `${selection.x}px`,
            transform: 'translateX(-50%)',
            opacity: 1
        });

        // Lock body scroll
        const originalOverflow = document.body.style.overflow;
        document.body.style.overflow = 'hidden';

        return () => {
            document.body.style.overflow = originalOverflow;
        };
    }, [selection]);

    return (
        <div
            ref={popupRef}
            className="selection-popup fixed z-[60] bg-white rounded-lg shadow-xl border border-slate-200 p-3 w-80"
            style={style}
        >
            <div className="mb-2 text-xs font-semibold text-slate-500 flex items-center gap-1">
                <FilePlus size={14} />
                Add Note to Obsidian
            </div>
            <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Enter your thoughts..."
                className="w-full text-sm p-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 mb-3 resize-none h-24"
                autoFocus
            />
            <button
                onClick={onSave}
                className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium py-2 rounded-md transition-colors"
            >
                <Save size={16} />
                Save to Obsidian
            </button>
            {/* Arrow - simplified to be hidden or centered */}
        </div>
    );
};


export default SummaryPanel;
