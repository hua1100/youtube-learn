import React, { useState, useEffect } from 'react';
import { X, Plus, Loader2, Rss } from 'lucide-react';

const ChannelManager = ({ onClose }) => {
    const [channels, setChannels] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(true);
    const [adding, setAdding] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        fetch('/api/channels')
            .then(r => r.json())
            .then(data => { setChannels(data); setLoading(false); })
            .catch(() => setLoading(false));
    }, []);

    const handleAdd = async () => {
        const url = input.trim().replace(/\/$/, '');
        if (!url) return;
        setAdding(true);
        setError('');
        try {
            const res = await fetch('/api/channels', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || '新增失敗');
            setChannels(data.channels);
            setInput('');
        } catch (e) {
            setError(e.message);
        } finally {
            setAdding(false);
        }
    };

    const handleRemove = async (url) => {
        try {
            const res = await fetch('/api/channels', {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail);
            setChannels(data.channels);
        } catch (e) {
            setError(e.message);
        }
    };

    const displayName = (url) => {
        const m = url.match(/@([^/]+)/);
        return m ? `@${m[1]}` : url;
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
            <div
                className="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden"
                onClick={e => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
                    <div className="flex items-center gap-2">
                        <Rss size={18} className="text-indigo-500" />
                        <h2 className="font-bold text-slate-900">管理追蹤頻道</h2>
                    </div>
                    <button onClick={onClose} className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-400">
                        <X size={18} />
                    </button>
                </div>

                {/* Add Input */}
                <div className="px-6 py-4 border-b border-slate-100">
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && handleAdd()}
                            placeholder="貼上 YouTube 頻道網址，例如 https://www.youtube.com/@channel"
                            className="flex-1 text-sm px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                        />
                        <button
                            onClick={handleAdd}
                            disabled={adding || !input.trim()}
                            className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {adding ? <Loader2 size={15} className="animate-spin" /> : <Plus size={15} />}
                            新增
                        </button>
                    </div>
                    {error && <p className="mt-2 text-xs text-rose-500">{error}</p>}
                </div>

                {/* Channel List */}
                <div className="px-6 py-4 max-h-80 overflow-y-auto">
                    {loading ? (
                        <div className="flex justify-center py-8">
                            <Loader2 size={24} className="animate-spin text-indigo-400" />
                        </div>
                    ) : channels.length === 0 ? (
                        <p className="text-sm text-slate-400 text-center py-8">尚未追蹤任何頻道</p>
                    ) : (
                        <ul className="space-y-2">
                            {channels.map(url => (
                                <li key={url} className="flex items-center justify-between gap-3 px-3 py-2.5 bg-slate-50 rounded-lg group">
                                    <div className="min-w-0">
                                        <p className="text-sm font-semibold text-slate-800 truncate">{displayName(url)}</p>
                                        <p className="text-xs text-slate-400 truncate">{url}</p>
                                    </div>
                                    <button
                                        onClick={() => handleRemove(url)}
                                        className="shrink-0 p-1.5 text-slate-400 hover:text-rose-500 hover:bg-rose-50 rounded-lg opacity-0 group-hover:opacity-100 transition-all"
                                    >
                                        <X size={15} />
                                    </button>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>

                <div className="px-6 py-3 bg-slate-50 border-t border-slate-100">
                    <p className="text-xs text-slate-400">新增後下次排程檢查時會自動抓取新影片</p>
                </div>
            </div>
        </div>
    );
};

export default ChannelManager;
