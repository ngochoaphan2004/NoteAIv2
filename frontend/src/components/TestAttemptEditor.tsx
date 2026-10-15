import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api, EvaluationResponse } from "../services/api";
import {
  Send,
  CheckCircle2,
  XCircle,
  ShieldCheck,
  RotateCw,
  FileText,
  Trash2,
  Sparkles,
} from "lucide-react";

export const TestAttemptEditor: React.FC = () => {
  const [attemptText, setAttemptText] = useState("");
  const [skill, setSkill] = useState("listening");

  const evalMutation = useMutation({
    mutationFn: () => api.evaluateAttempt(attemptText, skill),
  });

  const result: EvaluationResponse | undefined = evalMutation.data;

  const loadSample = (type: "listening" | "reading") => {
    if (type === "listening") {
      setSkill("listening");
      setAttemptText(
        `# Bài Làm Mẫu Test 1 Listening (Cam 18)\n1 dw307yz\n2 24_4\n3 dentist\n4 parking\n5 13_july\n6 0770_105\n7 clarkson\n8 0844_777_888\n9 police\n10 10.30`
      );
    } else {
      setSkill("reading");
      setAttemptText(
        `# Bài Làm Mẫu Reading Passage 3 (Cam 18)\n27 b\n28 a\n29 c\n30 d\n31 true\n32 false\n33 not given`
      );
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Khung Soạn Thảo Shorthand Syntax */}
      <div className="bg-white dark:bg-apple-cardDark p-6 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-apple-textLight dark:text-apple-textDark flex items-center gap-2">
              <FileText className="w-5 h-5 text-apple-blue" />
              <span>Đối Soát & Phân Tích Bài Thi (Shorthand Syntax)</span>
            </h2>
            <p className="text-xs text-apple-subtextLight dark:text-apple-subtextDark mt-1">
              Nhập nhanh đáp án hoặc kết quả đối chiếu theo cú pháp tốc ký để AI lưu trữ và phân tích.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={skill}
              onChange={(e) => setSkill(e.target.value)}
              className="px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-xs font-semibold"
            >
              <option value="listening">Listening</option>
              <option value="reading">Reading</option>
              <option value="writing">Writing</option>
              <option value="speaking">Speaking</option>
            </select>

            <button
              onClick={() => evalMutation.mutate()}
              disabled={evalMutation.isPending || !attemptText.trim()}
              className="px-5 py-2 bg-apple-blue text-white rounded-xl text-xs font-semibold hover:bg-apple-blueHover transition flex items-center gap-1.5 shadow-sm disabled:opacity-50"
            >
              {evalMutation.isPending ? (
                <>
                  <RotateCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Đang phân tích...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Đối Soát Bài Làm</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Hướng dẫn cú pháp & Quick preset buttons */}
        <div className="flex flex-wrap items-center justify-between gap-2 p-3 bg-gray-50 dark:bg-gray-800/40 rounded-2xl border border-gray-100 dark:border-gray-800 text-xs">
          <div className="flex flex-wrap items-center gap-3 text-apple-subtextLight dark:text-apple-subtextDark">
            <span>
              💡 Đúng: <code className="bg-white dark:bg-gray-700 px-1 py-0.5 rounded font-mono text-apple-blue">3 dentist</code>
            </span>
            <span>
              Sai: <code className="bg-white dark:bg-gray-700 px-1 py-0.5 rounded font-mono text-apple-blue">1 sai - đúng / lý do</code>
            </span>
            <span>
              Bỏ trống: <code className="bg-white dark:bg-gray-700 px-1 py-0.5 rounded font-mono text-apple-blue">16 - b / lý do</code>
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => loadSample("listening")}
              className="px-2.5 py-1 text-[11px] font-medium bg-white dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg transition"
            >
              Mẫu Listening
            </button>
            <button
              onClick={() => loadSample("reading")}
              className="px-2.5 py-1 text-[11px] font-medium bg-white dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg transition"
            >
              Mẫu Reading
            </button>
            {attemptText && (
              <button
                onClick={() => setAttemptText("")}
                className="p-1 text-gray-400 hover:text-red-500 rounded-lg transition"
                title="Xóa trắng"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        <textarea
          rows={7}
          value={attemptText}
          onChange={(e) => setAttemptText(e.target.value)}
          className="w-full p-4 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl text-sm font-mono text-apple-textLight dark:text-apple-textDark focus:outline-none focus:ring-2 focus:ring-apple-blue transition"
          placeholder="Dán hoặc nhập cú pháp tốc ký bài thi tại đây..."
        />
      </div>

      {/* Kết Quả Đối Soát & Phân Tích */}
      {result && (
        <div className="bg-white dark:bg-apple-cardDark p-6 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm space-y-6 animate-fadeIn">
          {/* Banner Tuân Thủ Nguyên Tắc Vàng Hoặc Kết Quả Điểm */}
          {!result.score_fraction ? (
            <div className="p-4 bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900 rounded-2xl flex items-start gap-3">
              <ShieldCheck className="w-5 h-5 text-apple-blue shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-bold text-apple-blue uppercase tracking-wider">
                  Nguyên Tắc Vàng: Lưu Trữ Trung Thực Bài Làm
                </h4>
                <p className="text-xs text-blue-800 dark:text-blue-300 mt-1">
                  Người học chưa cung cấp bảng đáp án chính thức. Hệ thống{" "}
                  <strong>tuyệt đối không tự đoán đúng/sai hay tự chấm điểm</strong>. Toàn bộ câu trả lời của bạn đã được ghi nhận vào bảng đối soát bên dưới.
                </p>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-between p-4 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 rounded-2xl">
              <div>
                <span className="text-xs font-bold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider block">
                  Kết Quả Đối Soát Chính Thức
                </span>
                <span className="text-2xl font-black text-emerald-800 dark:text-emerald-300">
                  {result.score_fraction} Câu Đúng
                </span>
              </div>
              {result.band_score !== undefined && (
                <div className="text-right">
                  <span className="text-xs text-emerald-600 dark:text-emerald-400 block font-semibold">
                    Band Score Ước Lượng
                  </span>
                  <span className="text-3xl font-black text-apple-blue">
                    {result.band_score}
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Bảng Chi Tiết Từng Câu Hỏi */}
          <div className="overflow-x-auto rounded-xl border border-gray-100 dark:border-gray-800">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-50 dark:bg-gray-800/60">
                <tr className="border-b border-gray-100 dark:border-gray-800 text-apple-subtextLight dark:text-apple-subtextDark font-semibold uppercase tracking-wider">
                  <th className="py-2.5 px-3 w-16">Câu</th>
                  <th className="py-2.5 px-3">Đáp Án Của Bạn</th>
                  <th className="py-2.5 px-3">Đáp Án Đúng</th>
                  <th className="py-2.5 px-3 w-28">Trạng Thái</th>
                  <th className="py-2.5 px-3">Loại Bẫy / Phân Tích</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800/50">
                {result.questions.map((q) => (
                  <tr
                    key={q.question_number}
                    className="hover:bg-gray-50/50 dark:hover:bg-gray-800/30"
                  >
                    <td className="py-3 px-3 font-bold text-center">{q.question_number}</td>
                    <td className="py-3 px-3 font-mono font-medium">
                      {q.user_answer || (
                        <span className="text-gray-400 italic">(bỏ trống)</span>
                      )}
                    </td>
                    <td className="py-3 px-3 font-mono text-apple-subtextLight dark:text-apple-subtextDark">
                      {q.correct_answer || (
                        <span className="text-gray-400 italic">Chưa nhập</span>
                      )}
                    </td>
                    <td className="py-3 px-3">
                      {q.is_correct === true && (
                        <span className="inline-flex items-center gap-1 text-emerald-600 font-bold">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Đúng
                        </span>
                      )}
                      {q.is_correct === false && (
                        <span className="inline-flex items-center gap-1 text-red-500 font-bold">
                          <XCircle className="w-3.5 h-3.5" /> Sai
                        </span>
                      )}
                      {q.is_correct === null && (
                        <span className="text-gray-400 italic text-[11px]">
                          Đã ghi nhận
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-apple-subtextLight dark:text-apple-subtextDark">
                      {q.trap_type || q.explanation || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Micro-drills Đề Xuất */}
          {result.recommended_drills?.length > 0 && (
            <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-2xl border border-gray-100 dark:border-gray-800">
              <h4 className="text-xs font-bold text-apple-textLight dark:text-apple-textDark uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-apple-blue" />
                <span>Bài Tập Micro-Session Đề Xuất (30-35 Phút):</span>
              </h4>
              <ul className="list-disc list-inside text-xs text-apple-subtextLight dark:text-apple-subtextDark space-y-1">
                {result.recommended_drills.map((drill, idx) => (
                  <li key={idx}>{drill}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TestAttemptEditor;
