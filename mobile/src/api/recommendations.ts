import { apiClient } from './client';

export interface Recommendation {
  id: number;
  occasion: string | null;
  weather_condition: string | null;
  weather_temp_celsius: number | null;
  season: string | null;
  item_ids: number[];
  rationale: string | null;
  accessory_suggestion: string | null;
  gpt_model_used: string | null;
  accepted: boolean | null;
  user_rating: number | null;
  created_at: string;
}

export interface VisualizationJob {
  id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  image_url: string | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface WardrobeSummary {
  total_items: number;
  items_worn_at_least_once: number;
  utilization_rate: number;
  unworn_30_days: number;
  unworn_60_days: number;
  unworn_90_days: number;
  sustainability_score: number;
  item_stats: Array<{
    item_id: number;
    item_name: string;
    category: string;
    wear_count: number;
    last_worn: string | null;
    cost_per_wear: number | null;
    days_since_last_worn: number | null;
  }>;
}

export const recommendationsApi = {
  create: (occasion: string, use_weather = true) =>
    apiClient
      .post<Recommendation>('/recommendations', { occasion, use_weather })
      .then((r) => r.data),

  list: (params?: { limit?: number; offset?: number }) =>
    apiClient.get<Recommendation[]>('/recommendations', { params }).then((r) => r.data),

  submitFeedback: (id: number, data: { accepted?: boolean; user_rating?: number }) =>
    apiClient.put<Recommendation>(`/recommendations/${id}/feedback`, data).then((r) => r.data),

  requestVisualization: (recommendation_id: number) =>
    apiClient
      .post<VisualizationJob>('/visualizations', { recommendation_id })
      .then((r) => r.data),

  getVisualizationStatus: (jobId: string) =>
    apiClient.get<VisualizationJob>(`/visualizations/${jobId}`).then((r) => r.data),

  getAnalyticsSummary: () =>
    apiClient.get<WardrobeSummary>('/analytics/summary').then((r) => r.data),

  getUnwornItems: (days = 30) =>
    apiClient.get(`/analytics/unworn?days=${days}`).then((r) => r.data),
};
