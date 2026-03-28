import { apiClient } from './client';

export interface WardrobeItem {
  id: number;
  user_id: string;
  name: string;
  category: string;
  description: string | null;
  subcategory: string | null;
  primary_color: string | null;
  pattern: string | null;
  formality: string | null;
  image_url: string | null;
  purchase_cost: number | null;
  clip_processed: boolean;
  attributes: Record<string, unknown> | null;
  tags: Array<{ id: number; name: string }>;
  created_at: string;
  updated_at: string;
}

export interface WardrobeItemCreate {
  name: string;
  category: string;
  description?: string;
  primary_color?: string;
  pattern?: string;
  formality?: string;
  image_url?: string;
  image_s3_key?: string;
  purchase_cost?: number;
}

export interface UsageLog {
  id: number;
  item_id: number;
  occasion: string | null;
  notes: string | null;
  worn_at: string;
}

export const wardrobeApi = {
  getUploadUrl: (extension = 'jpg') =>
    apiClient
      .get<{ presigned_post: Record<string, unknown>; object_key: string; public_url: string }>(
        `/wardrobe/upload-url?extension=${extension}`
      )
      .then((r) => r.data),

  listItems: (params?: { category?: string; limit?: number; offset?: number }) =>
    apiClient.get<WardrobeItem[]>('/wardrobe/items', { params }).then((r) => r.data),

  getItem: (id: number) =>
    apiClient.get<WardrobeItem>(`/wardrobe/items/${id}`).then((r) => r.data),

  createItem: (data: WardrobeItemCreate) =>
    apiClient.post<WardrobeItem>('/wardrobe/items', data).then((r) => r.data),

  updateItem: (id: number, data: Partial<WardrobeItemCreate>) =>
    apiClient.put<WardrobeItem>(`/wardrobe/items/${id}`, data).then((r) => r.data),

  deleteItem: (id: number) => apiClient.delete(`/wardrobe/items/${id}`),

  logWear: (id: number, data: { occasion?: string; notes?: string }) =>
    apiClient.post<UsageLog>(`/wardrobe/items/${id}/wear`, data).then((r) => r.data),

  getWearHistory: (id: number) =>
    apiClient.get<UsageLog[]>(`/wardrobe/items/${id}/wear-history`).then((r) => r.data),

  search: (query: string, limit = 10) =>
    apiClient
      .post<WardrobeItem[]>('/wardrobe/search', { query, limit })
      .then((r) => r.data),
};
