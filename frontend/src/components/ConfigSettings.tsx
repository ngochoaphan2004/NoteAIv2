import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  api,
  SystemConfig,
  UpdateConfigPayload,
  TestLLMResponse,
  CronStatus,
} from "../services/api";
import {
  Settings,
  Sparkles,
  Clock,
  Network,
  Terminal,
  HardDrive,
  Save,
  CheckCircle2,
  AlertCircle,
  Eye,
  EyeOff,
  Play,
  RotateCw,
  Cpu,
  Layers,
  ShieldCheck,
  Download,
  Server,
  Zap,
} from "lucide-react";

const SUGGESTED_GEMINI_MODELS = [
  "gemini-flash-lite-latest",
  "gemini-3.5-flash-lite",
  "gemini-3.8-flash",
  "gemini-flash-latest",
  "gemini-3.5-flash",
];

const SUGGESTED_OPENAI_MODELS = [
  "gpt-4o-mini",
  "gpt-4o",
  "gpt-3.5-turbo",
];

export const ConfigSettings: React.FC = () => {
  const queryClient = useQueryClient();

  // Form states
  const [provider, setProvider] = useState<string>("gemini");
  const [primaryModel, setPrimaryModel] = useState<string>("gemini-flash-lite-latest");
  const [fallbackModels, setFallbackModels] = useState<string>("");
  const [geminiApiKey, setGeminiApiKey] = useState<string>("");
  const [openaiApiKey, setOpenaiApiKey] = useState<string>("");
  const [watchdogEnabled, setWatchdogEnabled] = useState<boolean>(true);

  // UI interaction states
  const [showGeminiKey, setShowGeminiKey] = useState<boolean>(false);
  const [showOpenaiKey, setShowOpenaiKey] = useState<boolean>(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);
  const [saveErrorMsg, setSaveErrorMsg] = useState<string | null>(null);

  // Test LLM state
  const [testResult, setTestResult] = useState<TestLLMResponse | null>(null);
  const [isTestingLLM, setIsTestingLLM] = useState<boolean>(false);

  // Cron test state
  const [cronLogs, setCronLogs] = useState<string[]>([]);
  const [isTriggeringCron, setIsTriggeringCron] = useState<boolean>(false);

  // System logs viewer state
  const [activeLogType, setActiveLogType] = useState<"app" | "error">("app");

  // 1. Fetch current config
  const { data: config, isLoading: isConfigLoading, refetch: refetchConfig } = useQuery({
    queryKey: ["systemConfig"],
    queryFn: () => api.getConfig(),
  });

  // 2. Fetch cron status
  const { data: cronStatus, refetch: refetchCron } = useQuery({
    queryKey: ["cronStatus"],
    queryFn: () => api.getCronStatus(),
    refetchInterval: 15000,
  });

  // 3. Fetch server health metrics
  const { data: healthMetrics, refetch: refetchHealth } = useQuery({
    queryKey: ["healthMetrics"],
    queryFn: () => api.getHealthMetrics(),
  });

  // 4. Fetch system logs
  const { data: logData, isLoading: isLogLoading, refetch: refetchLogs } = useQuery({
    queryKey: ["systemLogs", activeLogType],
    queryFn: () => api.getLogs(activeLogType, 60),
    refetchInterval: 10000,
  });

  // Synchronize form when config loads
  useEffect(() => {
    if (config) {
      setProvider(config.llm_provider || "gemini");
      setPrimaryModel(config.llm_model || "gemini-1.5-flash");
      setFallbackModels(config.llm_models || "gemini-1.5-flash,gemini-2.0-flash,gemini-1.5-flash-8b,gemini-1.5-pro");
      setWatchdogEnabled(config.watchdog_enabled !== false);
    }
  }, [config]);

  // Synchronize cron logs if available
  useEffect(() => {
    if (cronStatus?.logs && cronStatus.logs.length > 0 && cronLogs.length === 0) {
      setCronLogs(cronStatus.logs);
    }
  }, [cronStatus]);

  // Mutation: Save Configuration
  const saveMutation = useMutation({
    mutationFn: (payload: UpdateConfigPayload) => api.updateConfig(payload),
    onSuccess: (res) => {
      setSaveSuccessMsg(res.message || "Đã lưu và cập nhật cấu hình thành công!");
      setSaveErrorMsg(null);
      setGeminiApiKey(""); // Reset input field after saving
      setOpenaiApiKey("");
      queryClient.invalidateQueries({ queryKey: ["systemConfig"] });
      setTimeout(() => setSaveSuccessMsg(null), 4000);
    },
    onError: (err: any) => {
      setSaveErrorMsg(err.message || "Có lỗi xảy ra khi lưu cấu hình.");
      setSaveSuccessMsg(null);
    },
  });

  const handleSaveConfig = () => {
    const payload: UpdateConfigPayload = {
      llm_provider: provider,
      llm_model: primaryModel,
      llm_models: fallbackModels,
      watchdog_enabled: watchdogEnabled,
    };
    if (geminiApiKey.trim()) {
      payload.gemini_api_key = geminiApiKey.trim();
    }
    if (openaiApiKey.trim()) {
      payload.openai_api_key = openaiApiKey.trim();
    }
    saveMutation.mutate(payload);
  };

  // Test LLM Connection
  const handleTestLLM = async () => {
    setIsTestingLLM(true);
    setTestResult(null);
    try {
      const res = await api.testLLM();
      setTestResult(res);
    } catch (err: any) {
      setTestResult({
        success: false,
        message: err.message || "Lỗi không xác định khi kết nối LLM.",
      });
    } finally {
      setIsTestingLLM(false);
    }
  };

  // Trigger Cronjob Now
  const handleTriggerCron = async () => {
    setIsTriggeringCron(true);
    try {
      const res = await api.triggerCron();
      if (res.result?.logs) {
        setCronLogs(res.result.logs);
      }
      refetchCron();
      refetchLogs();
    } catch (err: any) {
      setCronLogs((prev) => [...prev, `❌ Lỗi kích hoạt Cronjob: ${err.message}`]);
    } finally {
      setIsTriggeringCron(false);
    }
  };

  // Add/remove fallback model pill helper
  const handleTogglePill = (modelName: string) => {
    const currentList = fallbackModels
      .split(",")
      .map((m) => m.trim())
      .filter(Boolean);

    if (currentList.includes(modelName)) {
      setFallbackModels(currentList.filter((m) => m !== modelName).join(", "));
    } else {
      setFallbackModels([...currentList, modelName].join(", "));
    }
  };

  if (isConfigLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-3 text-apple-subtextLight dark:text-apple-subtextDark">
        <RotateCw className="w-6 h-6 animate-spin text-apple-blue" />
        <p className="text-sm font-medium">Đang tải cấu hình hệ thống...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12 animate-in fade-in duration-300">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-apple-cardDark p-6 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-blue-50 dark:bg-blue-950/40 text-apple-blue rounded-xl">
              <Settings className="w-5 h-5" />
            </div>
            <h1 className="text-lg font-bold tracking-tight">Cấu Hình & Quản Trị Hệ Thống</h1>
            <span className="px-2 py-0.5 text-[10px] font-bold bg-green-100 dark:bg-green-950 text-green-700 dark:text-green-300 rounded-full">
              Live Control
            </span>
          </div>
          <p className="text-xs text-apple-subtextLight dark:text-apple-subtextDark">
            Quản trị mô hình Cloud LLM, danh sách fallback rate-limit, lịch trình Cronjob Việt Nam và cổng mạng cố định.
          </p>
        </div>

        {/* Action Button */}
        <button
          onClick={handleSaveConfig}
          disabled={saveMutation.isPending}
          className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-apple-blue text-white text-xs font-semibold hover:bg-blue-600 active:scale-95 transition shadow-sm disabled:opacity-50"
        >
          {saveMutation.isPending ? (
            <RotateCw className="w-4 h-4 animate-spin" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          <span>Lưu Cấu Hình</span>
        </button>
      </div>

      {/* Notifications */}
      {saveSuccessMsg && (
        <div className="flex items-center gap-2.5 p-3.5 bg-green-50 dark:bg-green-950/40 border border-green-200 dark:border-green-800 rounded-xl text-green-800 dark:text-green-200 text-xs">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-green-600 dark:text-green-400" />
          <span>{saveSuccessMsg}</span>
        </div>
      )}

      {saveErrorMsg && (
        <div className="flex items-center gap-2.5 p-3.5 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-xl text-red-800 dark:text-red-200 text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-600 dark:text-red-400" />
          <span>{saveErrorMsg}</span>
        </div>
      )}

      {/* Main Grid: 2 Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ========================================================= */}
        {/* SECTION 1: LLM & FALLBACK CONFIGURATION                   */}
        {/* ========================================================= */}
        <div className="bg-white dark:bg-apple-cardDark p-5 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm space-y-5">
          <div className="flex items-center justify-between border-b border-gray-100 dark:border-gray-800/80 pb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-apple-blue" />
              <h2 className="text-sm font-bold">Mô Hình AI & Chuỗi Dự Phòng (Failover)</h2>
            </div>
            <button
              onClick={handleTestLLM}
              disabled={isTestingLLM}
              className="flex items-center gap-1.5 px-3 py-1 bg-blue-50 dark:bg-blue-950/40 text-apple-blue hover:bg-blue-100 dark:hover:bg-blue-900/60 rounded-lg text-xs font-semibold transition disabled:opacity-50"
            >
              {isTestingLLM ? (
                <RotateCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Zap className="w-3.5 h-3.5" />
              )}
              <span>Kiểm tra kết nối</span>
            </button>
          </div>

          {/* Test LLM Result Banner */}
          {testResult && (
            <div
              className={`p-3 rounded-xl border text-xs space-y-1 ${
                testResult.success
                  ? "bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-800 text-emerald-900 dark:text-emerald-100"
                  : "bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-800 text-red-900 dark:text-red-100"
              }`}
            >
              <div className="flex items-center justify-between font-semibold">
                <span className="flex items-center gap-1.5">
                  {testResult.success ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-red-600" />
                  )}
                  {testResult.message}
                </span>
                {testResult.latency_ms && (
                  <span className="font-mono text-[11px] bg-white/60 dark:bg-black/30 px-2 py-0.5 rounded">
                    {testResult.latency_ms} ms
                  </span>
                )}
              </div>
              {testResult.model_used && (
                <p className="text-[11px] opacity-80">
                  Mô hình phản hồi: <span className="font-mono font-bold">{testResult.model_used}</span>
                </p>
              )}
            </div>
          )}

          {/* Provider Selection */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-apple-subtextLight dark:text-apple-subtextDark">
              Nhà Cung Cấp LLM (Cloud API)
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => {
                  setProvider("gemini");
                  setPrimaryModel("gemini-1.5-flash");
                }}
                className={`p-3 rounded-xl border text-left flex items-center justify-between transition ${
                  provider === "gemini"
                    ? "border-apple-blue bg-blue-50/50 dark:bg-blue-950/20 text-apple-blue font-bold shadow-sm"
                    : "border-gray-200 dark:border-gray-800 text-gray-700 dark:text-gray-300 hover:border-gray-300"
                }`}
              >
                <div>
                  <div className="text-xs font-bold">Google Gemini</div>
                  <div className="text-[10px] font-normal text-apple-subtextLight dark:text-apple-subtextDark">
                    Tốc độ cao, miễn phí token
                  </div>
                </div>
                {provider === "gemini" && <CheckCircle2 className="w-4 h-4 text-apple-blue" />}
              </button>

              <button
                type="button"
                onClick={() => {
                  setProvider("openai");
                  setPrimaryModel("gpt-4o-mini");
                }}
                className={`p-3 rounded-xl border text-left flex items-center justify-between transition ${
                  provider === "openai"
                    ? "border-apple-blue bg-blue-50/50 dark:bg-blue-950/20 text-apple-blue font-bold shadow-sm"
                    : "border-gray-200 dark:border-gray-800 text-gray-700 dark:text-gray-300 hover:border-gray-300"
                }`}
              >
                <div>
                  <div className="text-xs font-bold">OpenAI GPT</div>
                  <div className="text-[10px] font-normal text-apple-subtextLight dark:text-apple-subtextDark">
                    Độ chính xác cao
                  </div>
                </div>
                {provider === "openai" && <CheckCircle2 className="w-4 h-4 text-apple-blue" />}
              </button>
            </div>
          </div>

          {/* Primary Model */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-apple-subtextLight dark:text-apple-subtextDark">
              Mô Hình Chính (Khởi Đầu Mọi Lượt Gọi)
            </label>
            <input
              type="text"
              value={primaryModel}
              onChange={(e) => setPrimaryModel(e.target.value)}
              placeholder="e.g. gemini-1.5-flash"
              className="w-full px-3.5 py-2 text-xs rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 focus:outline-none focus:ring-2 focus:ring-apple-blue"
            />
          </div>

          {/* Fallback Models Chain */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-apple-subtextLight dark:text-apple-subtextDark">
                Danh Sách Mô Hình Dự Phòng Khi Chạm Rate Limit (LLM_MODELS)
              </label>
            </div>
            <textarea
              rows={2}
              value={fallbackModels}
              onChange={(e) => setFallbackModels(e.target.value)}
              placeholder="gemini-1.5-flash,gemini-2.0-flash,gemini-1.5-flash-8b,gemini-1.5-pro"
              className="w-full px-3.5 py-2 text-xs font-mono rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 focus:outline-none focus:ring-2 focus:ring-apple-blue"
            />
            {/* Quick Pills */}
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="text-[10px] text-apple-subtextLight dark:text-apple-subtextDark mr-1">
                Gợi ý nhanh:
              </span>
              {(provider === "gemini" ? SUGGESTED_GEMINI_MODELS : SUGGESTED_OPENAI_MODELS).map(
                (model) => {
                  const isSelected = fallbackModels.includes(model);
                  return (
                    <button
                      key={model}
                      type="button"
                      onClick={() => handleTogglePill(model)}
                      className={`text-[10px] px-2 py-0.5 rounded-lg border font-mono transition ${
                        isSelected
                          ? "bg-blue-100 dark:bg-blue-900/40 text-apple-blue border-blue-300 dark:border-blue-700 font-bold"
                          : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-700 hover:border-gray-300"
                      }`}
                    >
                      {isSelected ? "✓ " : "+ "}
                      {model}
                    </button>
                  );
                }
              )}
            </div>
          </div>

          {/* API Keys */}
          <div className="space-y-3 pt-2 border-t border-gray-100 dark:border-gray-800/80">
            {/* Gemini API Key */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-apple-subtextLight dark:text-apple-subtextDark flex items-center gap-1.5">
                  <span>Gemini API Key</span>
                  {config?.has_gemini_key ? (
                    <span className="px-1.5 py-0.2 text-[9px] bg-green-100 dark:bg-green-950 text-green-700 dark:text-green-300 rounded font-bold">
                      Đã cấu hình ({config.gemini_api_key_masked})
                    </span>
                  ) : (
                    <span className="px-1.5 py-0.2 text-[9px] bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300 rounded font-bold">
                      Chưa cấu hình
                    </span>
                  )}
                </label>
              </div>
              <div className="relative">
                <input
                  type={showGeminiKey ? "text" : "password"}
                  value={geminiApiKey}
                  onChange={(e) => setGeminiApiKey(e.target.value)}
                  placeholder="Nhập API Key mới để cập nhật..."
                  className="w-full px-3.5 py-2 pr-10 text-xs font-mono rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 focus:outline-none focus:ring-2 focus:ring-apple-blue"
                />
                <button
                  type="button"
                  onClick={() => setShowGeminiKey(!showGeminiKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showGeminiKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            {/* OpenAI API Key */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-apple-subtextLight dark:text-apple-subtextDark flex items-center gap-1.5">
                  <span>OpenAI API Key (Tùy chọn)</span>
                  {config?.has_openai_key ? (
                    <span className="px-1.5 py-0.2 text-[9px] bg-green-100 dark:bg-green-950 text-green-700 dark:text-green-300 rounded font-bold">
                      Đã cấu hình ({config.openai_api_key_masked})
                    </span>
                  ) : (
                    <span className="px-1.5 py-0.2 text-[9px] bg-gray-100 dark:bg-gray-800 text-gray-500 rounded font-semibold">
                      Chưa cấu hình
                    </span>
                  )}
                </label>
              </div>
              <div className="relative">
                <input
                  type={showOpenaiKey ? "text" : "password"}
                  value={openaiApiKey}
                  onChange={(e) => setOpenaiApiKey(e.target.value)}
                  placeholder="Nhập API Key mới để cập nhật..."
                  className="w-full px-3.5 py-2 pr-10 text-xs font-mono rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 focus:outline-none focus:ring-2 focus:ring-apple-blue"
                />
                <button
                  type="button"
                  onClick={() => setShowOpenaiKey(!showOpenaiKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showOpenaiKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* ========================================================= */}
        {/* SECTION 2: CRONJOB & SCHEDULER (VIETNAM TIMEZONE)        */}
        {/* ========================================================= */}
        <div className="bg-white dark:bg-apple-cardDark p-5 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm space-y-5">
          <div className="flex items-center justify-between border-b border-gray-100 dark:border-gray-800/80 pb-3">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-apple-blue" />
              <h2 className="text-sm font-bold">Lịch Trình Tự Động Định Kỳ (Cronjob)</h2>
            </div>
            <button
              onClick={handleTriggerCron}
              disabled={isTriggeringCron}
              className="flex items-center gap-1.5 px-3 py-1 bg-green-50 dark:bg-green-950/40 text-green-700 dark:text-green-300 hover:bg-green-100 dark:hover:bg-green-900/60 rounded-lg text-xs font-semibold transition disabled:opacity-50"
            >
              {isTriggeringCron ? (
                <RotateCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Play className="w-3.5 h-3.5" />
              )}
              <span>Chạy Thử Nghiệm Ngay</span>
            </button>
          </div>

          {/* Cron Information Cards */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-xl space-y-1">
              <span className="text-[11px] text-apple-subtextLight dark:text-apple-subtextDark">
                Múi Giờ Vận Hành
              </span>
              <div className="font-bold flex items-center gap-1.5 text-apple-blue font-mono">
                <span>Asia/Ho_Chi_Minh</span>
                <span className="text-[10px] px-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded font-semibold">
                  UTC+7
                </span>
              </div>
            </div>

            <div className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-xl space-y-1">
              <span className="text-[11px] text-apple-subtextLight dark:text-apple-subtextDark">
                Thời Gian Kích Hoạt
              </span>
              <div className="font-bold font-mono">
                23:59:00 Đêm (UTC+7)
              </div>
            </div>

            <div className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-xl space-y-1">
              <span className="text-[11px] text-apple-subtextLight dark:text-apple-subtextDark">
                Trạng Thái Daemon
              </span>
              <div className="font-semibold flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-apple-green animate-pulse" />
                <span>Đang hoạt động ngầm</span>
              </div>
            </div>

            <div className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-xl space-y-1">
              <span className="text-[11px] text-apple-subtextLight dark:text-apple-subtextDark">
                Lần Chạy Gần Nhất
              </span>
              <div className="font-mono text-[11px] truncate">
                {cronStatus?.last_run_time || "Chưa ghi nhận"}
              </div>
            </div>
          </div>

          {/* 3 Core Cron Tasks Description */}
          <div className="space-y-2 text-xs border border-gray-100 dark:border-gray-800 p-3 rounded-xl bg-blue-50/30 dark:bg-blue-950/20">
            <div className="font-bold text-apple-blue flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4" />
              <span>3 Tác Vụ Tự Động Định Kỳ Mỗi Đêm:</span>
            </div>
            <ul className="space-y-1 text-apple-subtextLight dark:text-apple-subtextDark pl-5 list-disc text-[11px]">
              <li>
                <strong>Quét & Đồng bộ Thẻ FSRS:</strong> Quét các file <code>vocab-*.md</code> trong vườn tri thức và nạp thẻ mới vào PostgreSQL.
              </li>
              <li>
                <strong>Kiểm Chứng Đồ Thị Tri Thức:</strong> Quét Dead Links và tính toàn vẹn liên kết Markdown theo AGENTS.md.
              </li>
              <li>
                <strong>Thống Kê Thẻ Ôn Tập Hôm Nay:</strong> Tính toán số lượng thẻ FSRS đến hạn để duy trì Retention Rate &gt;= 90%.
              </li>
            </ul>
          </div>

          {/* Live Cron Execution Console */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <label className="font-semibold text-apple-subtextLight dark:text-apple-subtextDark flex items-center gap-1.5">
                <Terminal className="w-3.5 h-3.5" />
                <span>Nhật Ký Thực Thi Cronjob</span>
              </label>
              {cronLogs.length > 0 && (
                <button
                  type="button"
                  onClick={() => setCronLogs([])}
                  className="text-[10px] text-gray-400 hover:text-gray-600"
                >
                  Xóa màn hình
                </button>
              )}
            </div>
            <div className="bg-gray-950 text-gray-200 p-3.5 rounded-xl font-mono text-[11px] h-36 overflow-y-auto space-y-1 border border-gray-800 shadow-inner">
              {cronLogs.length === 0 ? (
                <div className="text-gray-500 italic py-8 text-center">
                  Nhấn nút &quot;Chạy Thử Nghiệm Ngay&quot; để quan sát log thực thi thời gian thực của Cronjob.
                </div>
              ) : (
                cronLogs.map((log, idx) => (
                  <div key={idx} className="leading-relaxed whitespace-pre-wrap">
                    {log}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ========================================================= */}
      {/* SECTION 3: FIXED INFRASTRUCTURE PORTS & HARDWARE SAFETY   */}
      {/* ========================================================= */}
      <div className="bg-white dark:bg-apple-cardDark p-5 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-gray-100 dark:border-gray-800/80 pb-3">
          <div className="flex items-center gap-2">
            <Network className="w-4 h-4 text-apple-blue" />
            <h2 className="text-sm font-bold">Bản Đồ Cổng Mạng & An Toàn Phần Cứng (AGENTS.md)</h2>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-apple-subtextLight dark:text-apple-subtextDark">
            <Cpu className="w-3.5 h-3.5 text-apple-blue" />
            <span>FastEmbed ONNX (CPU AVX2) | GPU VRAM Safe</span>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {/* PostgreSQL */}
          <div className="p-3 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/30 space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold">PostgreSQL 16</span>
              <span className="w-2 h-2 rounded-full bg-apple-green animate-pulse" />
            </div>
            <div className="text-base font-extrabold font-mono text-apple-blue">
              :5433
            </div>
            <p className="text-[10px] text-apple-subtextLight dark:text-apple-subtextDark">
              Host port cố định, tránh xung đột CVAT (:5432)
            </p>
          </div>

          {/* Qdrant */}
          <div className="p-3 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/30 space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold">Qdrant Vector DB</span>
              <span className="w-2 h-2 rounded-full bg-apple-green animate-pulse" />
            </div>
            <div className="text-base font-extrabold font-mono text-apple-blue">
              :6333 / 6334
            </div>
            <p className="text-[10px] text-apple-subtextLight dark:text-apple-subtextDark">
              REST &amp; gRPC CPU Search
            </p>
          </div>

          {/* FastAPI */}
          <div className="p-3 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/30 space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold">FastAPI Gateway</span>
              <span className="w-2 h-2 rounded-full bg-apple-blue animate-pulse" />
            </div>
            <div className="text-base font-extrabold font-mono text-apple-blue">
              :8000
            </div>
            <p className="text-[10px] text-apple-subtextLight dark:text-apple-subtextDark">
              Core Runtime &amp; REST API
            </p>
          </div>

          {/* Quartz v4 */}
          <div className="p-3 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/30 space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold">Quartz v4 SSG</span>
              <span className="w-2 h-2 rounded-full bg-purple-500 animate-pulse" />
            </div>
            <div className="text-base font-extrabold font-mono text-purple-600">
              :8088
            </div>
            <p className="text-[10px] text-apple-subtextLight dark:text-apple-subtextDark">
              Digital Garden Preview
            </p>
          </div>

          {/* React SPA */}
          <div className="p-3 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/30 space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold">Vite React SPA</span>
              <span className="w-2 h-2 rounded-full bg-apple-green animate-pulse" />
            </div>
            <div className="text-base font-extrabold font-mono text-apple-blue">
              :5173
            </div>
            <p className="text-[10px] text-apple-subtextLight dark:text-apple-subtextDark">
              Giao diện người dùng
            </p>
          </div>
        </div>
      </div>

      {/* ========================================================= */}
      {/* SECTION 4: SERVER HEALTH & LIVE LOGS VIEWER              */}
      {/* ========================================================= */}
      <div className="bg-white dark:bg-apple-cardDark p-5 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-gray-100 dark:border-gray-800/80 pb-3">
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-apple-blue" />
            <h2 className="text-sm font-bold">Giám Sát Máy Chủ &amp; Nhật Ký Trực Tuyến</h2>
          </div>

          {/* Health & Disk Info */}
          {healthMetrics?.disk && (
            <div className="flex items-center gap-4 text-xs font-mono text-apple-subtextLight dark:text-apple-subtextDark">
              <div className="flex items-center gap-1.5">
                <HardDrive className="w-3.5 h-3.5 text-apple-blue" />
                <span>
                  Đĩa trống: <strong>{healthMetrics.disk.free_gb} GB</strong> ({healthMetrics.disk.free_percentage}) / {healthMetrics.disk.total_gb} GB
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Watchdog Switch + Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-gray-50 dark:bg-gray-800/40 p-3 rounded-xl text-xs">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-apple-blue" />
            <div>
              <span className="font-semibold">Watchdog File Listener: </span>
              <span className="text-apple-subtextLight dark:text-apple-subtextDark">
                Tự động re-index vector và FSRS khi file Markdown trong <code>content/</code> thay đổi.
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setWatchdogEnabled(!watchdogEnabled)}
            className={`px-3 py-1.5 rounded-lg font-semibold transition ${
              watchdogEnabled
                ? "bg-green-100 dark:bg-green-950 text-green-700 dark:text-green-300"
                : "bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400"
            }`}
          >
            {watchdogEnabled ? "Đang Bật (Enabled)" : "Đã Tắt (Disabled)"}
          </button>
        </div>

        {/* Live Logs Viewer */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            {/* Log Type Selector */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setActiveLogType("app")}
                className={`px-3 py-1 rounded-lg font-semibold transition ${
                  activeLogType === "app"
                    ? "bg-apple-blue text-white shadow-sm"
                    : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400"
                }`}
              >
                app.log (Hoạt động chung)
              </button>
              <button
                type="button"
                onClick={() => setActiveLogType("error")}
                className={`px-3 py-1 rounded-lg font-semibold transition ${
                  activeLogType === "error"
                    ? "bg-red-500 text-white shadow-sm"
                    : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400"
                }`}
              >
                error.log (Lỗi máy chủ)
              </button>
            </div>

            {/* Actions: Refresh & Download */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => refetchLogs()}
                className="flex items-center gap-1 text-[11px] text-gray-500 hover:text-gray-800 dark:hover:text-gray-200"
              >
                <RotateCw className="w-3 h-3" />
                <span>Làm mới</span>
              </button>
              <a
                href={`/api/v1/system/logs/download?file_name=${activeLogType}.log`}
                download
                className="flex items-center gap-1 text-[11px] text-apple-blue hover:underline"
              >
                <Download className="w-3 h-3" />
                <span>Tải file log</span>
              </a>
            </div>
          </div>

          {/* Console Box */}
          <div className="bg-gray-950 text-gray-200 p-4 rounded-xl font-mono text-[11px] h-48 overflow-y-auto space-y-1 border border-gray-800 shadow-inner">
            {isLogLoading ? (
              <div className="flex items-center justify-center h-full text-gray-500">
                <RotateCw className="w-4 h-4 animate-spin mr-2" />
                Đang tải dữ liệu log...
              </div>
            ) : logData?.lines && logData.lines.length > 0 ? (
              logData.lines.map((line, idx) => {
                let colorClass = "text-gray-300";
                if (line.includes("ERROR") || line.includes("Exception") || line.includes("Failed")) {
                  colorClass = "text-red-400 font-bold";
                } else if (line.includes("WARNING")) {
                  colorClass = "text-amber-400";
                } else if (line.includes("CRON") || line.includes("HTTP")) {
                  colorClass = "text-emerald-400";
                }
                return (
                  <div key={idx} className={`${colorClass} leading-relaxed whitespace-pre-wrap`}>
                    {line}
                  </div>
                );
              })
            ) : (
              <div className="text-gray-500 italic py-12 text-center">
                Chưa có dữ liệu log trong file này.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
export default ConfigSettings;

