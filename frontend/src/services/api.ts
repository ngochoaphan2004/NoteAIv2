const API_BASE = '/api/v1';

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
    if (!res.ok) throw new Error('Không thể tải danh sách thẻ đến hạn');
    return res.json();
  },

  async reviewCard(cardId: string, rating: number): Promise<any> {
    const res = await fetch(`${API_BASE}/flashcards/${cardId}/review?rating=${rating}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Lỗi cập nhật đánh giá thẻ');
    return res.json();
  },

  async syncMarkdownCards(): Promise<any> {
    const res = await fetch(`${API_BASE}/flashcards/sync-markdown`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Lỗi đồng bộ thẻ từ Markdown');
    return res.json();
  },

  async getStats(): Promise<FlashcardStats> {
    const res = await fetch(`${API_BASE}/flashcards/stats`);
    if (!res.ok) throw new Error('Không thể tải thống kê FSRS');
    return res.json();
  },

  // RAG Search
  async searchRAG(query: string, limit = 5): Promise<any[]> {
    const res = await fetch(`${API_BASE}/rag/query?query=${encodeURIComponent(query)}&limit=${limit}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Lỗi truy vấn Vector DB');
    return res.json();
  },

  // Agents
  async evaluateAttempt(text: string, skill = 'listening'): Promise<EvaluationResponse> {
    const res = await fetch(`${API_BASE}/agents/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ attempt_text: text, skill }),
    });
    if (!res.ok) throw new Error('Lỗi khi chấm bài');
    return res.json();
  },

  async generatePlan(weekNumber = 2): Promise<any> {
    const res = await fetch(`${API_BASE}/agents/plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ week_number: weekNumber }),
    });
    if (!res.ok) throw new Error('Lỗi tạo kế hoạch thích ứng');
    return res.json();
  },
};
