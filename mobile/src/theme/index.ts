export const colors = {
  primary: '#6c63ff',       // deep purple — brand accent
  primaryDark: '#4a43cc',
  secondary: '#ff6584',     // warm pink
  background: '#0f0f1a',    // near-black background
  surface: '#1a1a2e',       // card surface
  surfaceLight: '#252545',  // lighter card
  text: '#f0f0f5',          // primary text
  textMuted: '#9898b0',     // secondary text
  border: '#2e2e50',
  success: '#4caf50',
  warning: '#ff9800',
  error: '#f44336',
  white: '#ffffff',
  black: '#000000',
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const typography = {
  h1: { fontSize: 28, fontWeight: '700' as const, color: colors.text },
  h2: { fontSize: 22, fontWeight: '700' as const, color: colors.text },
  h3: { fontSize: 18, fontWeight: '600' as const, color: colors.text },
  body: { fontSize: 15, fontWeight: '400' as const, color: colors.text },
  caption: { fontSize: 12, fontWeight: '400' as const, color: colors.textMuted },
  label: { fontSize: 13, fontWeight: '500' as const, color: colors.textMuted },
};

export const radius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  full: 9999,
};
