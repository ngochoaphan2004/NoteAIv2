import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import {
  RefreshCw,
  BookOpen,
  Clock,
  Award,
  Activity,
  Database,
} from "lucide-react";

export const StatsDashboard: React.FC = () => {
  const queryClient = useQueryClient();

  const {
    data: stats,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ["flashcards", "stats"],
    queryFn: () => api.getStats(),
  });

  const syncMutation = useMutation({
    mutationFn: () => api.syncMarkdownCards(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["flashcards"] });
      alert(
        `Đồng bộ thành công! Đã nạp ${data.cards_added} thẻ mới và cập nhật ${data.cards_updated} thẻ từ ${data.files_scanned} file markdown.`,
      );
    },
    onError: (err: any) => {
      alert(`Lỗi đồng bộ: ${err.message}`);
    },
  });

  if (isLoading || !stats) {
    return (
      <div className="flex justify-center p-12">
        <div className="w-8 h-8 border-4 border-apple-blue border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header & Sync Button */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-white dark:bg-apple-cardDark p-4 sm:p-6 rounded-2xl sm:rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-apple-textLight dark:text-apple-textDark">
            Động Cơ Trí Nhớ FSRS v4 & Viễn Trắc Tri Thức
          </h2>
          <p className="text-xs text-apple-subtextLight dark:text-apple-subtextDark mt-1">
            Mô hình toán học DSR (Difficulty, Stability, Retrievability) lưu trữ
            trong PostgreSQL
          </p>
        </div>
        <button
          onClick={() => syncMutation.mutate()}
          disabled={syncMutation.isPending}
          className="w-full sm:w-auto justify-center px-4 sm:px-5 py-2.5 bg-apple-blue text-white rounded-xl text-xs font-semibold hover:bg-apple-blueHover transition flex items-center gap-2 shadow-sm disabled:opacity-50"
        >
          <RefreshCw
            className={`w-4 h-4 ${syncMutation.isPending ? "animate-spin" : ""}`}
          />
          {syncMutation.isPending
            ? "Đang đồng bộ..."
            : "Đồng Bộ Từ Markdown (SSOT)"}
        </button>
      </div>

      {/* Grid 4 Thẻ Chỉ Số */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-apple-cardDark p-5 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm">
          <div className="flex items-center gap-2 text-apple-subtextLight dark:text-apple-subtextDark text-xs font-semibold mb-2">
            <BookOpen className="w-4 h-4 text-apple-blue" /> Tổng Thẻ Kho Từ
          </div>
          <div className="text-3xl font-extrabold text-apple-textLight dark:text-apple-textDark">
            {stats.total_cards}
          </div>
          <div className="text-[11px] text-apple-subtextLight dark:text-apple-subtextDark mt-1">
            Từ vựng học thuật IELTS
          </div>
        </div>

        <div className="bg-white dark:bg-apple-cardDark p-5 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm">
          <div className="flex items-center gap-2 text-apple-subtextLight dark:text-apple-subtextDark text-xs font-semibold mb-2">
            <Clock className="w-4 h-4 text-apple-orange" /> Đến Hạn Hôm Nay
          </div>
          <div className="text-3xl font-extrabold text-apple-orange">
            {stats.due_today}
          </div>
          <div className="text-[11px] text-apple-subtextLight dark:text-apple-subtextDark mt-1">
            Cần ôn theo chu kỳ FSRS
          </div>
        </div>

        <div className="bg-white dark:bg-apple-cardDark p-5 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm">
          <div className="flex items-center gap-2 text-apple-subtextLight dark:text-apple-subtextDark text-xs font-semibold mb-2">
            <Award className="w-4 h-4 text-apple-green" /> Tỷ Lệ Ghi Nhớ (R)
          </div>
          <div className="text-3xl font-extrabold text-apple-green">
            {stats.retention_rate}%
          </div>
          <div className="text-[11px] text-apple-subtextLight dark:text-apple-subtextDark mt-1">
            Mục tiêu chuẩn: &gt;= 90%
          </div>
        </div>

        <div className="bg-white dark:bg-apple-cardDark p-5 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm">
          <div className="flex items-center gap-2 text-apple-subtextLight dark:text-apple-subtextDark text-xs font-semibold mb-2">
            <Activity className="w-4 h-4 text-purple-500" /> Tổng Lượt Ôn
          </div>
          <div className="text-3xl font-extrabold text-apple-textLight dark:text-apple-textDark">
            {stats.total_reviews}
          </div>
          <div className="text-[11px] text-apple-subtextLight dark:text-apple-subtextDark mt-1">
            Lịch sử tương tác review_logs
          </div>
        </div>
      </div>

      {/* Phân bổ trạng thái thẻ FSRS */}
      <div className="bg-white dark:bg-apple-cardDark p-6 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm">
        <h3 className="text-sm font-bold text-apple-textLight dark:text-apple-textDark uppercase tracking-wider mb-4">
          Phân Bổ Vòng Đời Thẻ (FSRS Memory Lifecycle)
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {Object.entries(stats.states || {}).map(([state, count]) => (
            <div
              key={state}
              className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl"
            >
              <span className="text-xs font-semibold text-apple-subtextLight dark:text-apple-subtextDark block mb-1">
                {state}
              </span>
              <span className="text-xl font-bold text-apple-textLight dark:text-apple-textDark">
                {count}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
