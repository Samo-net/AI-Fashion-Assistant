/**
 * Axios API Client
 * ================
 * Central HTTP client for all backend requests.
 * - Attaches Firebase ID token as Bearer on every request
 * - Handles 401 by refreshing token and retrying once
 * - Surfaces structured API errors to callers
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import auth from '@react-native-firebase/auth';
import Constants from 'expo-constants';

const BASE_URL =
  (Constants.expoConfig?.extra?.apiBaseUrl as string) ?? 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Request interceptor: attach Firebase ID token ──────────────────────────
apiClient.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
  const user = auth().currentUser;
  if (user) {
    const token = await user.getIdToken(false);
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response interceptor: refresh token on 401 ────────────────────────────
apiClient.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const user = auth().currentUser;
      if (user) {
        const freshToken = await user.getIdToken(true); // force refresh
        original.headers.Authorization = `Bearer ${freshToken}`;
        return apiClient(original);
      }
    }
    return Promise.reject(error);
  }
);

// ── Typed API error helper ─────────────────────────────────────────────────
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail ?? error.message;
  }
  return String(error);
}
