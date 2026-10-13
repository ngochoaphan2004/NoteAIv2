import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '../services/api';
import { Search, FileText, Sparkles } from 'lucide-react';

export const RAGSearch: React.FC = () => {
  const [query, setQuery] = useState('space junk collision mitigation');
  const [results, setResults] = useState<any[]>([]);

  const searchMutation = useMutation({
    mutationFn: () => api.searchRAG(query, 5),
    onSuccess: (data) => setResults(data),
    onError: (err: any) => alert(`Lỗi tìm kiếm: ${err.message}`),
  });

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Search Input Box */}
      <div className="bg-white dark:bg-apple-cardDark p-6 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm">
        <h2 className="text-xl font-bold text-apple-textLight dark:text-apple-textDark mb-1">
          Truy Vấn Ngữ Nghĩa Kho Tri Thức (Qdrant Vector DB)
        </h2>
        <p className="text-xs text-apple-subtextLight dark:text-apple-subtextDark mb-4">
          Vector Embeddings chạy CPU qua FastEmbed (BAAI/bge-small-en-v1.5) tìm kiếm theo độ tương đồng Cosine
        </p>

        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && searchMutation.mutate()}
              placeholder="Nhập khái niệm, từ vựng hoặc chủ đề IELTS cần tra cứu..."
              className="w-full pl-10 pr-4 py-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-apple-blue"
            />
          </div>
          <button
            onClick={() => searchMutation.mutate()}
            disabled={searchMutation.isPending || !query.trim()}
            className="px-5 py-2.5 bg-apple-blue text-white rounded-xl text-xs font-semibold hover:bg-apple-blueHover transition flex items-center gap-1.5 shadow-sm disabled:opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5" />
            {searchMutation.isPending ? 'Đang tìm...' : 'Tìm Kiếm'}
          </button>
        </div>
      </div>

      {/* Kết Quả Tìm Kiếm */}
      {results.length > 0 && (
        <div className="space-y-4">
          {results.map((hit, idx) => (
            <div
              key={idx}
              className="bg-white dark:bg-apple-cardDark p-5 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm"
            >
              <div className="flex items-center justify-between text-xs text-apple-subtextLight dark:text-apple-subtextDark mb-2">
                <span className="flex items-center gap-1.5 font-medium text-apple-blue">
                  <FileText className="w-3.5 h-3.5" />
                  {hit.source_file} &gt; {hit.heading}
                </span>
                <span className="bg-blue-50 dark:bg-blue-950/40 text-apple-blue px-2 py-0.5 rounded-full font-mono text-[11px]">
                  Similarity: {(hit.score * 100).toFixed(1)}%
                </span>
              </div>
              <p className="text-xs text-apple-textLight dark:text-apple-textDark leading-relaxed whitespace-pre-line bg-gray-50 dark:bg-gray-900/50 p-3.5 rounded-xl font-mono">
                {hit.content}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
