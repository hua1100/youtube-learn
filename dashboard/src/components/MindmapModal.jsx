import React, { useState, useEffect, useRef, useCallback } from 'react';
import { X, Loader2, AlertCircle, Download, Maximize2, Minimize2 } from 'lucide-react';
import { createPortal } from 'react-dom';

const MindmapModal = ({ isOpen, onClose, videoId, videoTitle }) => {
    const [mermaidCode, setMermaidCode] = useState(null);
    const [renderedSvg, setRenderedSvg] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const containerRef = useRef(null);

    useEffect(() => {
        if (isOpen && videoId) {
            fetchMindmap();
        }
        return () => {
            setMermaidCode(null);
            setRenderedSvg(null);
            setError(null);
            setIsFullscreen(false);
        };
    }, [isOpen, videoId]);

    useEffect(() => {
        if (mermaidCode) {
            renderMermaid();
        }
    }, [mermaidCode]);

    // 清理 Mermaid 語法中可能導致解析錯誤的字符
    const sanitizeMermaidCode = (code) => {
        return code.split('\n').map(line => {
            const indent = line.match(/^(\s*)/)[1];
            const content = line.trimStart();

            if (content.startsWith('root((')) {
                const match = content.match(/^root\(\((.+)\)\)$/);
                if (match) {
                    const innerText = match[1].replace(/[()[\]{}]/g, ' ').trim();
                    return `${indent}root((${innerText}))`;
                }
            }

            if (content === 'mindmap' || content.startsWith('root(')) {
                return line;
            }

            const cleaned = content.replace(/[()[\]{}]/g, ' ').replace(/\s+/g, ' ').trim();
            return indent + cleaned;
        }).join('\n');
    };

    const fetchMindmap = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await fetch(`/api/mindmap/${videoId}`);
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || '生成失敗');
            }
            const data = await response.json();
            const cleanedCode = sanitizeMermaidCode(data.mermaid);
            setMermaidCode(cleanedCode);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    const renderMermaid = async () => {
        if (!mermaidCode) return;

        try {
            const mermaid = (await import('mermaid')).default;
            mermaid.initialize({
                startOnLoad: false,
                theme: 'default',
                mindmap: {
                    useMaxWidth: true,
                    padding: 20
                }
            });

            const id = `mindmap-${Date.now()}`;
            const { svg } = await mermaid.render(id, mermaidCode);
            setRenderedSvg(svg);
        } catch (err) {
            console.error('Mermaid render error:', err);
            setError(`渲染錯誤: ${err.message}`);
        }
    };

    const handleDownload = useCallback(() => {
        if (!renderedSvg) return;

        const blob = new Blob([renderedSvg], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `mindmap_${videoId}.svg`;
        a.click();
        URL.revokeObjectURL(url);
    }, [renderedSvg, videoId]);

    const handleClose = useCallback(() => {
        setIsFullscreen(false);
        onClose();
    }, [onClose]);

    if (!isOpen) return null;

    const modalContent = (
        <div
            className="fixed inset-0 z-[9999] flex items-center justify-center"
            style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
            onClick={handleClose}
        >
            <div
                className="bg-white shadow-2xl flex flex-col overflow-hidden"
                style={{
                    width: isFullscreen ? '100vw' : '90vw',
                    height: isFullscreen ? '100vh' : '80vh',
                    maxWidth: isFullscreen ? 'none' : '1000px',
                    borderRadius: isFullscreen ? '0' : '16px',
                }}
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 shrink-0 bg-white">
                    <div className="flex-1 min-w-0">
                        <h2 className="text-lg font-bold text-slate-900 truncate">
                            🧠 心智圖
                        </h2>
                        <p className="text-sm text-slate-500 truncate">
                            {videoTitle}
                        </p>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                        {renderedSvg && (
                            <>
                                <button
                                    onClick={handleDownload}
                                    className="p-2 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg"
                                    title="下載 SVG"
                                >
                                    <Download size={18} />
                                </button>
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        setIsFullscreen(!isFullscreen);
                                    }}
                                    className="p-2 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg"
                                    title={isFullscreen ? "縮小" : "全螢幕"}
                                >
                                    {isFullscreen ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
                                </button>
                            </>
                        )}
                        <button
                            onClick={handleClose}
                            className="p-2 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg"
                        >
                            <X size={18} />
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-auto p-6 bg-slate-50">
                    {isLoading && (
                        <div className="flex flex-col items-center justify-center h-full gap-4">
                            <Loader2 size={48} className="animate-spin text-indigo-500" />
                            <p className="text-slate-600 font-medium">
                                正在生成心智圖...
                            </p>
                            <p className="text-sm text-slate-400">
                                首次生成約需 10-30 秒
                            </p>
                        </div>
                    )}

                    {error && (
                        <div className="flex flex-col items-center justify-center h-full gap-4">
                            <AlertCircle size={48} className="text-rose-500" />
                            <p className="text-rose-600 font-medium text-center max-w-md">
                                {error}
                            </p>
                            <button
                                onClick={fetchMindmap}
                                className="px-4 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600"
                            >
                                重試
                            </button>
                        </div>
                    )}

                    {!isLoading && !error && renderedSvg && (
                        <div
                            ref={containerRef}
                            className="w-full h-full flex items-center justify-center"
                            dangerouslySetInnerHTML={{ __html: renderedSvg }}
                        />
                    )}
                </div>
            </div>
        </div>
    );

    // 使用 Portal 將 Modal 渲染到 body，避免被父層影響
    return createPortal(modalContent, document.body);
};

export default MindmapModal;
