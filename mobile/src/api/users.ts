import { apiClient } from './client';

export interface UserProfile {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  body_type: string | null;
  skin_tone: string | null;
  style_preference: string | null;
  city: string | null;
  state: string | null;
  gdpr_consent: boolean;
  consent_timestamp: string | null;
  created_at: string;
}

export interface UserProfileUpdate {
  display_name?: string;
  body_type?: string;
  skin_tone?: string;
  style_preference?: string;
  city?: string;
  state?: string;
  avatar_url?: string;
}

export const usersApi = {
  sync: (data: { email: string; display_name?: string; gdpr_consent: boolean }) =>
    apiClient.post<UserProfile>('/users/sync', data).then((r) => r.data),

  getMe: () => apiClient.get<UserProfile>('/users/me').then((r) => r.data),

  updateMe: (updates: UserProfileUpdate) =>
    apiClient.put<UserProfile>('/users/me', updates).then((r) => r.data),

  updateConsent: (gdpr_consent: boolean) =>
    apiClient.put<UserProfile>('/users/me/consent', { gdpr_consent }).then((r) => r.data),

  deleteAccount: () => apiClient.delete('/users/me'),
};
