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
  Bot,
  FolderCheck,
  PenTool,
  BookOpen,
} from "lucide-react";

export const TestAttemptEditor: React.FC = () => {
  const [attemptText, setAttemptText] = useState("");
  const [skill, setSkill] = useState("listening");
  const [targetFile, setTargetFile] = useState("auto");
  const [taskId, setTaskId] = useState("task-1");
  const [writingTab, setWritingTab] = useState<"diff" | "clean" | "rubric">("diff");

  const evalMutation = useMutation({
    mutationFn: () =>
      api.evaluateAttempt(
        attemptText,
        skill,
        targetFile === "auto" ? undefined : targetFile,
        skill === "writing" ? taskId : undefined
      ),
  });

  const result: EvaluationResponse | undefined = evalMutation.data;

  const loadSample = (type: "listening" | "reading" | "writing") => {
    if (type === "listening") {
      setSkill("listening");
      setTargetFile("plans/week-01/test-1-listening-p1-p2.md");
      setAttemptText(
        `1 dw307yz\n2 24th April\n3 dentist\n4 car\n5 Claxby\n6 late\n7 evening\n8 supermarket\n9 pollution\n10 storage`
      );
    } else if (type === "reading") {
      setSkill("reading");
      setTargetFile("plans/week-01/test-1-reading-p3.md");
      setAttemptText(
        `27 D\n28 B\n29 G\n30 C\n31 YES\n32 NO\n33 NOT GIVEN\n34 YES\n35 C\n36 A\n37 D\n38 A\n39 B\n40 C`
      );
    } else {
      setSkill("writing");
      setTargetFile("plans/week-01/test-1-writing.md");
      setAttemptText(
        `The line graph illustrates the proportion of urban residents in four Asian nations between 1970 and 2020, with forecasts up to 2040. Overall, all four countries experienced an increase in urbanization over the period.`
      );
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Khung Soạn Thảo Shorthand Syntax & Target Note */}
      <div className="bg-white dark:bg-apple-cardDark p-6 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-apple-textLight dark:text-apple-textDark flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-apple-blue" />
              <span>Chấm Điểm & Đối Soát Đáp Án Cambridge 18</span>
            </h2>
            <p className="text-xs text-apple-subtextLight dark:text-apple-subtextDark mt-1">
              Chấm điểm tự động và bóc tách bẫy lỗi sai trực tiếp từ bộ đáp án chính thức Cambridge IELTS 18 (JSON Database).
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
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

            {skill === "writing" && (
              <select
                value={taskId}
                onChange={(e) => setTaskId(e.target.value)}
                className="px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-xs font-semibold text-apple-textLight dark:text-apple-textDark"
                title="Chọn phần thi Writing Task 1 hoặc Task 2"
              >
                <option value="task-1">Task 1 (Báo cáo)</option>
                <option value="task-2">Task 2 (Bài luận)</option>
              </select>
            )}

            <select
              value={targetFile}
              onChange={(e) => setTargetFile(e.target.value)}
              className="px-3 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-xs font-semibold text-apple-textLight dark:text-apple-textDark max-w-[200px]"
              title="Chọn file Markdown ghi chú để cập nhật Bảng Đối Soát"
            >
              <option value="auto">🎯 Tự động phát hiện file</option>
              <option value="plans/week-01/test-1-listening-p1-p2.md">[19/10] Test 1 Listening P1-P2</option>
              <option value="plans/week-01/test-1-listening-p3-p4.md">[20/10] Test 1 Listening P3-P4</option>
              <option value="plans/week-01/test-1-reading-p1-p2.md">[21/10] Reading Passage 1-2</option>
              <option value="plans/week-01/test-1-reading-p3.md">[22/10] Reading Passage 3</option>
              <option value="plans/week-01/test-1-writing.md">[23/10] Writing Task 1</option>
            </select>

            <button
              onClick={() => evalMutation.mutate()}
              disabled={evalMutation.isPending || !attemptText.trim()}
              className="px-5 py-2 bg-apple-blue text-white rounded-xl text-xs font-semibold hover:bg-apple-blueHover transition flex items-center gap-1.5 shadow-sm disabled:opacity-50"
            >
              {evalMutation.isPending ? (
                <>
                  <RotateCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Đang chấm điểm...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Chấm Điểm Bài Làm</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Hướng dẫn cú pháp & Quick preset buttons */}
        <div className="flex flex-wrap items-center justify-between gap-2 p-3 bg-gray-50 dark:bg-gray-800/40 rounded-2xl border border-gray-100 dark:border-gray-800 text-xs">
          <div className="flex flex-wrap items-center gap-3 text-apple-subtextLight dark:text-apple-subtextDark">
            <span>
              💡 Cú pháp: <code className="bg-white dark:bg-gray-700 px-1.5 py-0.5 rounded font-mono text-apple-blue">1 dw307yz</code>
            </span>
            <span>
              <code className="bg-white dark:bg-gray-700 px-1.5 py-0.5 rounded font-mono text-apple-blue">2 24th April</code>
            </span>
            <span>
              <code className="bg-white dark:bg-gray-700 px-1.5 py-0.5 rounded font-mono text-apple-blue">31 true</code>
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
            <button
              onClick={() => loadSample("writing")}
              className="px-2.5 py-1 text-[11px] font-medium bg-white dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg transition"
            >
              Mẫu Writing
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
          placeholder="Dán hoặc nhập cú pháp tốc ký bài thi / bài viết luận tại đây..."
        />
      </div>

      {/* Thông báo lỗi nếu có */}
      {evalMutation.isError && (
        <div className="p-4 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 rounded-2xl flex items-center gap-2 text-xs text-red-600 dark:text-red-400">
          <XCircle className="w-4 h-4 shrink-0" />
          <span>Lỗi khi đối soát bài làm: {evalMutation.error?.message || "Không thể kết nối máy chủ"}</span>
        </div>
      )}

      {/* Kết Quả Đối Soát & Phân Tích */}
      {result && (
        <div className="bg-white dark:bg-apple-cardDark p-6 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm space-y-6 animate-fadeIn">
          {/* Thông báo đồng bộ SSOT vào file Markdown */}
          {result.updated_file && (
            <div className="p-3.5 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-2xl flex items-center justify-between text-xs text-emerald-800 dark:text-emerald-300">
              <div className="flex items-center gap-2">
                <FolderCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>
                  Đã cập nhật trung thực vào <strong>Bảng Đối Soát Bài Làm</strong> trong file:{" "}
                  <code className="font-mono bg-white dark:bg-emerald-900/50 px-2 py-0.5 rounded text-emerald-700 dark:text-emerald-300 font-semibold">
                    {result.updated_file}
                  </code>
                </span>
              </div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 bg-emerald-100 dark:bg-emerald-900/60 px-2.5 py-1 rounded-full">
                SSOT Đồng Bộ
              </span>
            </div>
          )}

          {/* Banner Kết Quả Chấm Điểm Cambridge 18 */}
          {result.score_fraction && (
            <div className="flex items-center justify-between p-4 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 rounded-2xl">
              <div>
                <span className="text-xs font-bold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider block">
                  Kết Quả Chấm Điểm Cambridge 18
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

          {/* Writing Visual Diff Tabs (Khi có kết quả sửa chi tiết từng cụm từ) */}
          {result.diff_html ? (
            <div className="space-y-4">
              <div className="flex items-center gap-2 border-b border-gray-200 dark:border-gray-800 pb-3 overflow-x-auto">
                <button
                  type="button"
                  onClick={() => setWritingTab("diff")}
                  className={`px-3.5 py-1.5 rounded-full text-xs font-semibold flex items-center gap-1.5 transition ${
                    writingTab === "diff"
                      ? "bg-apple-blue text-white shadow-sm"
                      : "bg-gray-100 dark:bg-gray-800 text-apple-subtextLight dark:text-apple-subtextDark hover:bg-gray-200"
                  }`}
                >
                  <PenTool className="w-3.5 h-3.5" />
                  <span>🔴🟢 Bản Sửa Trực Quan ({result.edits_count || 0} điểm)</span>
                </button>

                {result.clean_rewritten_text && (
                  <button
                    type="button"
                    onClick={() => setWritingTab("clean")}
                    className={`px-3.5 py-1.5 rounded-full text-xs font-semibold flex items-center gap-1.5 transition ${
                      writingTab === "clean"
                        ? "bg-apple-blue text-white shadow-sm"
                        : "bg-gray-100 dark:bg-gray-800 text-apple-subtextLight dark:text-apple-subtextDark hover:bg-gray-200"
                    }`}
                  >
                    <BookOpen className="w-3.5 h-3.5" />
                    <span>🌟 Bản Viết Lại Band 8.0+</span>
                  </button>
                )}

                {result.feedback && (
                  <button
                    type="button"
                    onClick={() => setWritingTab("rubric")}
                    className={`px-3.5 py-1.5 rounded-full text-xs font-semibold flex items-center gap-1.5 transition ${
                      writingTab === "rubric"
                        ? "bg-apple-blue text-white shadow-sm"
                        : "bg-gray-100 dark:bg-gray-800 text-apple-subtextLight dark:text-apple-subtextDark hover:bg-gray-200"
                    }`}
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>📊 Nhận Xét 4 Tiêu Chí IELTS</span>
                  </button>
                )}
              </div>

              {/* Tab Content */}
              {writingTab === "diff" && (
                <div className="p-5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl space-y-3">
                  <div className="flex items-center justify-between text-xs text-apple-subtextLight dark:text-apple-subtextDark">
                    <span className="font-semibold flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-apple-blue" />
                      Đối soát trực quan từng cụm từ (Đỏ: Lỗi / Xanh: Cải thiện Band 8.0+)
                    </span>
                    <span className="text-[11px] bg-blue-50 dark:bg-blue-950/60 text-apple-blue px-2 py-0.5 rounded-md font-mono">
                      FSRS Auto-Sync Ready
                    </span>
                  </div>
                  <div
                    className="text-sm leading-loose font-sans text-apple-textLight dark:text-apple-textDark p-2"
                    dangerouslySetInnerHTML={{ __html: result.diff_html }}
                  />
                </div>
              )}

              {writingTab === "clean" && result.clean_rewritten_text && (
                <div className="p-5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl space-y-3">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                    <BookOpen className="w-3.5 h-3.5" />
                    <span>Bản Viết Lại Hoàn Chỉnh Mẫu (Band 8.0+)</span>
                  </div>
                  <div className="text-sm leading-relaxed font-sans text-apple-textLight dark:text-apple-textDark whitespace-pre-line p-2">
                    {result.clean_rewritten_text}
                  </div>
                </div>
              )}

              {writingTab === "rubric" && result.feedback && (
                <div className="p-5 bg-gradient-to-br from-indigo-50/70 to-blue-50/50 dark:from-indigo-950/30 dark:to-blue-950/20 border border-indigo-100 dark:border-indigo-900/50 rounded-2xl space-y-3">
                  <div className="flex items-center gap-2 text-indigo-700 dark:text-indigo-400 font-bold text-xs uppercase tracking-wider">
                    <Sparkles className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                    <span>Nhận Xét & Chẩn Đoán 4 Tiêu Chí IELTS</span>
                  </div>
                  <div className="text-xs text-apple-textLight dark:text-apple-textDark leading-relaxed whitespace-pre-line font-sans">
                    {result.feedback}
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* Nhận Xét Cũ Cho Listening / Reading / Generic (Giữ nguyên 100%) */
            result.feedback && (
              <div className="p-5 bg-gradient-to-br from-indigo-50/70 to-blue-50/50 dark:from-indigo-950/30 dark:to-blue-950/20 border border-indigo-100 dark:border-indigo-900/50 rounded-2xl space-y-3">
                <div className="flex items-center gap-2 text-indigo-700 dark:text-indigo-400 font-bold text-xs uppercase tracking-wider">
                  <Sparkles className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                  <span>Nhận Xét & Chẩn Đoán Chuyên Sâu Từ AI</span>
                </div>
                <div className="text-xs text-apple-textLight dark:text-apple-textDark leading-relaxed whitespace-pre-line font-sans">
                  {result.feedback}
                </div>
              </div>
            )
          )}

          {/* Điểm Mạnh & Điểm Cần Cải Thiện */}
          {(result.strengths?.length > 0 || result.weaknesses?.length > 0) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {result.strengths?.length > 0 && (
                <div className="p-4 bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/30 rounded-2xl space-y-2">
                  <h5 className="text-xs font-bold text-emerald-700 dark:text-emerald-400 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Điểm Mạnh Ghi Nhận:</span>
                  </h5>
                  <ul className="list-disc list-inside text-xs text-apple-subtextLight dark:text-apple-subtextDark space-y-1">
                    {result.strengths.map((s, idx) => (
                      <li key={idx}>{s}</li>
                    ))}
                  </ul>
                </div>
              )}
              {result.weaknesses?.length > 0 && (
                <div className="p-4 bg-amber-50/50 dark:bg-amber-950/20 border border-amber-100 dark:border-amber-900/30 rounded-2xl space-y-2">
                  <h5 className="text-xs font-bold text-amber-700 dark:text-amber-400 flex items-center gap-1.5">
                    <XCircle className="w-3.5 h-3.5" />
                    <span>Điểm Cần Khắc Phục / Lưu Ý:</span>
                  </h5>
                  <ul className="list-disc list-inside text-xs text-apple-subtextLight dark:text-apple-subtextDark space-y-1">
                    {result.weaknesses.map((w, idx) => (
                      <li key={idx}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Bảng Chi Tiết Từng Câu Hỏi (cho Listening / Reading) */}
          {result.questions?.length > 0 && (
            <div className="overflow-x-auto rounded-xl border border-gray-100 dark:border-gray-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-gray-50 dark:bg-gray-800/60">
                  <tr className="border-b border-gray-100 dark:border-gray-800 text-apple-subtextLight dark:text-apple-subtextDark font-semibold uppercase tracking-wider">
                    <th className="py-2.5 px-3 w-16 text-center">Câu</th>
                    <th className="py-2.5 px-3">Đáp Án Của Bạn</th>
                    <th className="py-2.5 px-3">Đáp Án Đúng</th>
                    <th className="py-2.5 px-3 w-28 text-center">Trạng Thái</th>
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
                        {q.user_answer ? (
                          <span className="text-apple-blue font-semibold">{q.user_answer}</span>
                        ) : (
                          <span className="text-gray-400 italic">(bỏ trống)</span>
                        )}
                      </td>
                      <td className="py-3 px-3 font-mono text-apple-subtextLight dark:text-apple-subtextDark">
                        {q.correct_answer || (
                          <span className="text-gray-400 italic">Chưa nhập</span>
                        )}
                      </td>
                      <td className="py-3 px-3 text-center">
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
                            ⚪ Đã ghi nhận
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
          )}

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
