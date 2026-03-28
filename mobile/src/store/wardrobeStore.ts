import { create } from 'zustand';
import { wardrobeApi, WardrobeItem, WardrobeItemCreate } from '@/api/wardrobe';

interface WardrobeState {
  items: WardrobeItem[];
  loading: boolean;
  error: string | null;

  fetchItems: (category?: string) => Promise<void>;
  addItem: (data: WardrobeItemCreate) => Promise<WardrobeItem>;
  removeItem: (id: number) => Promise<void>;
  logWear: (id: number, occasion?: string) => Promise<void>;
  search: (query: string) => Promise<WardrobeItem[]>;
  clearError: () => void;
}

export const useWardrobeStore = create<WardrobeState>((set, get) => ({
  items: [],
  loading: false,
  error: null,

  clearError: () => set({ error: null }),

  fetchItems: async (category) => {
    set({ loading: true, error: null });
    try {
      const items = await wardrobeApi.listItems({ category, limit: 100 });
      set({ items });
    } catch (e: any) {
      set({ error: e.message });
    } finally {
      set({ loading: false });
    }
  },

  addItem: async (data) => {
    set({ loading: true, error: null });
    try {
      const item = await wardrobeApi.createItem(data);
      set((state) => ({ items: [item, ...state.items] }));
      return item;
    } catch (e: any) {
      set({ error: e.message });
      throw e;
    } finally {
      set({ loading: false });
    }
  },

  removeItem: async (id) => {
    try {
      await wardrobeApi.deleteItem(id);
      set((state) => ({ items: state.items.filter((i) => i.id !== id) }));
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  logWear: async (id, occasion) => {
    try {
      await wardrobeApi.logWear(id, { occasion });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  search: async (query) => {
    return wardrobeApi.search(query);
  },
}));
