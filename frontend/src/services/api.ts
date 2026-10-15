const API_BASE = "/api/v1";

export interface FlashcardItem {
  id: string;
  front: string;
  back: string;
  ipa?: string;
  part_of_speech?: string;
  synonyms?: string;
  tags?: string;
  stability: number;
  difficulty: number;
  state: string;
  reps: number;
  due: string;
  preview_intervals: {
    again: string;
    hard: string;
    good: string;
    easy: string;
  };
}

export interface FlashcardStats {
  total_cards: number;
  due_today: number;
  states: Record<string, number>;
  total_reviews: number;
  retention_rate: number;
}

export interface QuestionResult {
  question_number: number;
  user_answer: string;
  correct_answer?: string;
  is_correct?: boolean;
  trap_type?: string;
  explanation?: string;
}

export interface ContextSource {
  source_file: string;
  heading: string;
  content: string;
  score: number;
}

export interface AskResponse {
  question: string;
  answer: string;
  sources: ContextSource[];
  model_used?: string;
}

export interface EvaluationResponse {
  score_fraction?: string;
  band_score?: number;
  strengths: string[];
  weaknesses: string[];
  questions: QuestionResult[];
  recommended_drills: string[];
}

export const api = {
  // Flashcards FSRS
  async getDueCards(limit = 20): Promise<FlashcardItem[]> {
    const res = await fetch(`${API_BASE}/flashcards/due?limit=${limit}`);
    if (!res.ok) throw new Error("Không thể tải danh sách thẻ đến hạn");
    return res.json();
  },

  async reviewCard(cardId: string, rating: number): Promise<any> {
    const res = await fetch(
      `${API_BASE}/flashcards/${cardId}/review?rating=${rating}`,
      {
        method: "POST",
      },
    );
    if (!res.ok) throw new Error("Lỗi cập nhật đánh giá thẻ");
    return res.json();
  },

  async syncMarkdownCards(): Promise<any> {
    const res = await fetch(`${API_BASE}/flashcards/sync-markdown`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("Lỗi đồng bộ thẻ từ Markdown");
    return res.json();
  },

  async getStats(): Promise<FlashcardStats> {
    const res = await fetch(`${API_BASE}/flashcards/stats`);
    if (!res.ok) throw new Error("Không thể tải thống kê FSRS");
    return res.json();
  },

  // RAG Q&A & Search
  async askRAG(question: string, topK = 4): Promise<AskResponse> {
    const res = await fetch(`${API_BASE}/rag/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, top_k: topK }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Lỗi hỏi đáp RAG");
    }
    return res.json();
  },

  async searchRAG(query: string, limit = 5): Promise<any[]> {
    const res = await fetch(
      `${API_BASE}/rag/query?query=${encodeURIComponent(query)}&limit=${limit}`,
      {
        method: "POST",
      },
    );
    if (!res.ok) throw new Error("Lỗi truy vấn Vector DB");
    return res.json();
  },

  async reindexRAG(): Promise<{ status: string; files_indexed: number; total_chunks: number }> {
    const res = await fetch(`${API_BASE}/rag/reindex`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("Lỗi lập chỉ mục lại Vector DB");
    return res.json();
  },

  // Agents
  async evaluateAttempt(
    text: string,
    skill = "listening",
  ): Promise<EvaluationResponse> {
    const res = await fetch(`${API_BASE}/agents/evaluate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ attempt_text: text, skill }),
    });
    if (!res.ok) throw new Error("Lỗi khi chấm bài");
    return res.json();
  },

  async generatePlan(weekNumber = 2): Promise<any> {
    const res = await fetch(`${API_BASE}/agents/plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ week_number: weekNumber }),
    });
    if (!res.ok) throw new Error("Lỗi tạo kế hoạch thích ứng");
    return res.json();
  },

  // System Configuration & Monitoring
  async getConfig(): Promise<SystemConfig> {
    const res = await fetch(`${API_BASE}/system/config`);
    if (!res.ok) throw new Error("Không thể tải cấu hình hệ thống");
    return res.json();
  },

  async updateConfig(payload: UpdateConfigPayload): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${API_BASE}/system/config`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Không thể cập nhật cấu hình hệ thống");
    return res.json();
  },

  async testLLM(): Promise<TestLLMResponse> {
    try {
      const res = await fetch(`${API_BASE}/system/test-llm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        return {
          success: false,
          message: data?.detail || data?.message || `Lỗi máy chủ (${res.status}): ${res.statusText}`,
          error: data?.error || `HTTP ${res.status}`,
        };
      }
      return data || {
        success: false,
        message: "Phản hồi không hợp lệ từ máy chủ",
      };
    } catch (err: any) {
      return {
        success: false,
        message: err?.message || "Không thể kết nối đến máy chủ",
        error: String(err),
      };
    }
  },

  // Cronjob Scheduler
  async getCronStatus(): Promise<CronStatus> {
    const res = await fetch(`${API_BASE}/cron/status`);
    if (!res.ok) throw new Error("Không thể lấy trạng thái Cronjob");
    return res.json();
  },

  async triggerCron(): Promise<CronTriggerResult> {
    const res = await fetch(`${API_BASE}/cron/trigger`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("Lỗi kích hoạt Cronjob");
    return res.json();
  },

  // System Logs & Health
  async getLogs(logType: "app" | "error" = "app", lines = 100): Promise<LogResponse> {
    const res = await fetch(`${API_BASE}/system/logs?log_type=${logType}&lines=${lines}`);
    if (!res.ok) throw new Error("Không thể tải nhật ký máy chủ");
    return res.json();
  },

  async getHealthMetrics(): Promise<HealthMetrics> {
    const res = await fetch(`${API_BASE}/system/health-metrics`);
    if (!res.ok) throw new Error("Không thể lấy chỉ số sức khỏe máy chủ");
    return res.json();
  },

  // Study Plans & Daily Automation
  async getTodayPlan(): Promise<{
    today: string;
    week: string | null;
    skill: string;
    duration?: string;
    focus: string;
    steps?: string[];
    link: string;
    is_done: boolean;
    status: string;
  }> {
    const res = await fetch(`${API_BASE}/plans/today`);
    if (!res.ok) throw new Error("Không thể lấy thông tin kế hoạch hôm nay");
    return res.json();
  },

  async syncPlans(): Promise<{
    status: string;
    today: string;
    updated_files: string[];
  }> {
    const res = await fetch(`${API_BASE}/plans/sync`, { method: "POST" });
    if (!res.ok) throw new Error("Lỗi kích hoạt đồng bộ kế hoạch");
    return res.json();
  },
};

export interface SystemConfig {
  llm_provider: string;
  llm_model: string;
  llm_models: string;
  has_gemini_key: boolean;
  gemini_api_key_masked: string;
  has_openai_key: boolean;
  openai_api_key_masked: string;
  database_url: string;
  qdrant_url: string;
  qdrant_collection: string;
  content_dir: string;
  environment: string;
  watchdog_enabled: boolean;
  cron_timezone: string;
  cron_schedule: string;
  ports: {
    database_postgres: number;
    qdrant_rest: number;
    qdrant_grpc: number;
    fastapi_backend: number;
    quartz_preview: number;
    frontend_spa: number;
  };
}

export interface UpdateConfigPayload {
  llm_provider?: string;
  llm_model?: string;
  llm_models?: string;
  gemini_api_key?: string;
  openai_api_key?: string;
  watchdog_enabled?: boolean;
}

export interface TestLLMResponse {
  success: boolean;
  model_used?: string;
  latency_ms?: number;
  provider?: string;
  response?: string;
  message: string;
  error?: string;
}

export interface CronStatus {
  is_running: boolean;
  schedule: string;
  last_run_time: string | null;
  last_run_status: string;
  logs: string[];
}

export interface CronTriggerResult {
  message: string;
  result: {
    success: boolean;
    duration_seconds: number;
    executed_at: string;
    logs: string[];
  };
}

export interface HealthMetrics {
  status: string;
  log_directory: string;
  disk: {
    total_gb: number;
    used_gb: number;
    free_gb: number;
    free_percentage: string;
  };
}

export interface LogResponse {
  log_type: string;
  file: string;
  total_lines_returned: number;
  lines: string[];
}

