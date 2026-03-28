import { create } from 'zustand';
import auth from '@react-native-firebase/auth';
import { usersApi, UserProfile } from '@/api/users';

interface AuthState {
  user: UserProfile | null;
  firebaseReady: boolean;
  loading: boolean;
  error: string | null;

  // Actions
  signInWithEmail: (email: string, password: string) => Promise<void>;
  signUpWithEmail: (email: string, password: string, displayName: string) => Promise<void>;
  signOut: () => Promise<void>;
  syncProfile: () => Promise<void>;
  updateProfile: (updates: Partial<UserProfile>) => Promise<void>;
  setFirebaseReady: (ready: boolean) => void;
  setUser: (user: UserProfile | null) => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  firebaseReady: false,
  loading: false,
  error: null,

  setFirebaseReady: (ready) => set({ firebaseReady: ready }),

  setUser: (user) => set({ user }),

  clearError: () => set({ error: null }),

  signInWithEmail: async (email, password) => {
    set({ loading: true, error: null });
    try {
      await auth().signInWithEmailAndPassword(email, password);
      await get().syncProfile();
    } catch (e: any) {
      set({ error: e.message ?? 'Sign in failed.' });
      throw e;
    } finally {
      set({ loading: false });
    }
  },

  signUpWithEmail: async (email, password, displayName) => {
    set({ loading: true, error: null });
    try {
      const cred = await auth().createUserWithEmailAndPassword(email, password);
      await cred.user.updateProfile({ displayName });
      // Sync to backend with consent
      const profile = await usersApi.sync({
        email,
        display_name: displayName,
        gdpr_consent: true,
      });
      set({ user: profile });
    } catch (e: any) {
      set({ error: e.message ?? 'Sign up failed.' });
      throw e;
    } finally {
      set({ loading: false });
    }
  },

  signOut: async () => {
    set({ loading: true });
    try {
      await auth().signOut();
      set({ user: null });
    } finally {
      set({ loading: false });
    }
  },

  syncProfile: async () => {
    const fbUser = auth().currentUser;
    if (!fbUser) return;
    try {
      const profile = await usersApi.sync({
        email: fbUser.email!,
        display_name: fbUser.displayName ?? undefined,
        gdpr_consent: false,
      });
      set({ user: profile });
    } catch {
      // User may not exist yet — not a hard error
    }
  },

  updateProfile: async (updates) => {
    set({ loading: true, error: null });
    try {
      const updated = await usersApi.updateMe(updates);
      set({ user: updated });
    } catch (e: any) {
      set({ error: e.message });
      throw e;
    } finally {
      set({ loading: false });
    }
  },
}));
