import React, { useEffect, useState } from 'react';
import VideoCard from './VideoCard';
import SummaryPanel from './SummaryPanel';
import { Loader2, RefreshCw, Search, Filter } from 'lucide-react';

const Dashboard = () => {
    const [videos, setVideos] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Search & Filter State
    const [searchTerm, setSearchTerm] = useState("");
    const [selectedChannel, setSelectedChannel] = useState("All");

    // Derived State: Unique Channels
    const channels = ["All", ...new Set(videos.map(v => v.channel_title || "Unknown").filter(c => c))];

    // Derived State: Filtered Videos
    const filteredVideos = videos.filter(video => {
        const matchesSearch = (video.title || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
            (video.preview || "").toLowerCase().includes(searchTerm.toLowerCase());
        const matchesChannel = selectedChannel === "All" || (video.channel_title || "Unknown") === selectedChannel;
        return matchesSearch && matchesChannel;
    });

    // State for the selected video (Panel)
    const [selectedVideo, setSelectedVideo] = useState(null);

    const fetchVideos = async (isBackground = false) => {
        if (!isBackground) setLoading(true);
        try {
            const response = await fetch('/api/videos');
            if (!response.ok) {
                throw new Error('Failed to fetch videos');
            }
            const data = await response.json();
            setVideos(data);
            setError(null);
        } catch (err) {
            setError(err.message);
        } finally {
            if (!isBackground) setLoading(false);
        }
    };

    useEffect(() => {
        fetchVideos();
    }, []);

    // Handler to open summary
    const handleViewSummary = async (video) => {
        // Optimistic open with existing data
        setSelectedVideo({ ...video, isLoadingDetails: true });

        try {
            const response = await fetch(`/api/summary/${video.id}`);
            if (!response.ok) {
                throw new Error('Failed to load summary');
            }
            const data = await response.json();

            // Update selection with full content
            setSelectedVideo(prev =>
                prev && prev.id === video.id
                    ? { ...prev, fullContent: data.content, isLoadingDetails: false }
                    : prev
            );
        } catch (err) {
            console.error("Error fetching summary details:", err);
            setSelectedVideo(prev =>
                prev && prev.id === video.id
                    ? { ...prev, fullContent: "## Error\nCould not load full summary content.", isLoadingDetails: false }
                    : prev
            );
        }
    };

    const closePanel = () => {
        setSelectedVideo(null);
    };

    const [isUpdating, setIsUpdating] = useState(false);
    const triggerUpdate = async () => {
        setIsUpdating(true);
        try {
            // Trigger update
            await fetch('/api/refresh', { method: 'POST' });

            // Poll status until done
            const intervalId = setInterval(async () => {
                try {
                    // Check status
                    const statusRes = await fetch('/api/status');
                    const statusData = await statusRes.json();

                    // Fetch latest videos to update UI progressively (Silent refresh)
                    await fetchVideos(true);

                    // If finished
                    if (!statusData.is_updating) {
                        setIsUpdating(false);
                        clearInterval(intervalId);
                    }
                } catch (e) {
                    console.error("Polling error", e);
                    setIsUpdating(false);
                    clearInterval(intervalId);
                }
            }, 2000); // Check every 2 seconds

        } catch (e) {
            console.error("Update failed", e);
            setIsUpdating(false);
        }
    };

    if (loading) {
        return (
            <div className="h-full flex flex-col items-center justify-center text-slate-400">
                <Loader2 className="w-10 h-10 animate-spin mb-4 text-indigo-500" />
                <p className="font-medium animate-pulse">Loading intelligence...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="h-full flex flex-col items-center justify-center text-slate-500">
                <div className="bg-red-50 p-6 rounded-2xl border border-red-100 text-center max-w-md">
                    <h3 className="text-red-800 font-bold text-lg mb-2">Connection Error</h3>
                    <p className="text-sm mb-4">{error}</p>
                    <button
                        onClick={fetchVideos}
                        className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-semibold hover:bg-slate-50 hover:text-indigo-600 transition-all shadow-sm"
                    >
                        <RefreshCw size={16} /> Retry Connection
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="h-full">
            {/* Header Title */}
            <div className="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight mb-2">
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-violet-600">
                            Latest Insights
                        </span>
                    </h1>
                    <p className="text-slate-500 font-medium">
                        Monitor and summarize tech trends with AI precision.
                    </p>
                </div>
                <div className="flex items-center gap-4 text-sm text-slate-500">
                    <button
                        onClick={async () => {
                            if (confirm("⚠️ Are you sure you want to RESET the entire system?\nThis will delete all videos, summaries, and history to force a full re-ingestion.")) {
                                try {
                                    await fetch('/api/reset', { method: 'POST' });
                                    alert("System Reset Complete. Page will reload.");
                                    window.location.reload();
                                } catch (e) {
                                    alert("Reset failed: " + e);
                                }
                            }
                        }}
                        className="inline-flex items-center gap-2 px-3 py-1.5 bg-red-white border border-red-200 text-red-600 rounded-lg text-xs font-semibold hover:bg-red-50 transition-all shadow-sm"
                        title="Reset System & Clear Data"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-trash-2"><path d="M3 6h18" /><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" /><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" /><line x1="10" x2="10" y1="11" y2="17" /><line x1="14" x2="14" y1="11" y2="17" /></svg>
                        Reset
                    </button>
                    <button
                        onClick={triggerUpdate}
                        disabled={isUpdating}
                        className="inline-flex items-center gap-2 px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-semibold hover:bg-slate-50 hover:text-indigo-600 transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <RefreshCw size={14} className={isUpdating ? "animate-spin text-indigo-500" : ""} />
                        {isUpdating ? 'Updating...' : 'Update Data'}
                    </button>
                    <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${isUpdating ? 'bg-amber-400 animate-pulse' : 'bg-emerald-500'}`}></span>
                        {isUpdating ? 'Checking for updates...' : 'System Operational'}
                    </div>
                </div>
            </div>

            {/* Search and Filters */}
            <div className="mb-8 space-y-4">
                {/* Search Input */}
                <div className="relative max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                    <input
                        type="text"
                        placeholder="Search topics, summaries..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 bg-white/50 backdrop-blur-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all text-sm"
                    />
                </div>

                {/* Channel Chips */}
                <div className="flex flax-wrap gap-2 overflow-x-auto pb-2 scrollbar-none">
                    {channels.map(channel => (
                        <button
                            key={channel}
                            onClick={() => setSelectedChannel(channel)}
                            className={`
                                whitespace-nowrap px-3 py-1.5 rounded-full text-xs font-semibold transition-all border
                                ${selectedChannel === channel
                                    ? 'bg-indigo-600 text-white border-indigo-600 shadow-md shadow-indigo-200'
                                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50 hover:border-indigo-200'}
                            `}
                        >
                            {channel}
                        </button>
                    ))}
                </div>
            </div>

            {/* Setup Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pb-12">
                {filteredVideos.map((video) => (
                    <VideoCard
                        key={video.id}
                        video={video}
                        onViewSummary={() => handleViewSummary(video)}
                    />
                ))}
            </div>


            {videos.length === 0 && (
                <div className="text-center py-20 bg-white rounded-2xl border border-dashed border-slate-300">
                    <p className="text-slate-400 font-medium">No videos found in the database.</p>
                </div>
            )}

            {/* Side Panel for Detail View */}
            <SummaryPanel
                video={selectedVideo}
                onClose={closePanel}
            />
        </div>
    );
};

export default Dashboard;
