import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, typography, radius } from '@/theme';
import { recommendationsApi, Recommendation } from '@/api/recommendations';
import { getErrorMessage } from '@/api/client';

const OCCASION_ICONS: Record<string, string> = {
  casual: 'sunny-outline',
  work: 'briefcase-outline',
  church: 'heart-outline',
  'wedding-guest': 'rose-outline',
  'traditional-ceremony': 'musical-notes-outline',
  date: 'heart-circle-outline',
};

export default function HistoryScreen({ navigation }: any) {
  const [history, setHistory] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await recommendationsApi.list({ limit: 20 });
        setHistory(data);
      } catch (e) {
        setError(getErrorMessage(e));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.primary} size="large" />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.center}>
        <Ionicons name="warning-outline" size={36} color={colors.error} />
        <Text style={styles.errorText}>{error}</Text>
      </View>
    );
  }

  if (history.length === 0) {
    return (
      <View style={styles.center}>
        <Ionicons name="time-outline" size={48} color={colors.border} />
        <Text style={styles.emptyTitle}>No history yet</Text>
        <Text style={styles.emptySubtitle}>Your outfit recommendations will appear here.</Text>
      </View>
    );
  }

  const renderItem = ({ item }: { item: Recommendation }) => {
    const icon = OCCASION_ICONS[item.occasion ?? ''] ?? 'shirt-outline';
    const date = new Date(item.created_at).toLocaleDateString('en-NG', {
      day: 'numeric', month: 'short', year: 'numeric',
    });

    return (
      <TouchableOpacity
        style={styles.card}
        onPress={() => navigation.navigate('Visualization', { recommendationId: item.id })}
        activeOpacity={0.7}
      >
        <View style={styles.cardIcon}>
          <Ionicons name={icon as any} size={22} color={colors.primary} />
        </View>
        <View style={styles.cardBody}>
          <View style={styles.cardTop}>
            <Text style={styles.occasion}>{item.occasion?.replace('-', ' ') ?? 'Casual'}</Text>
            {item.accepted === true && (
              <Ionicons name="thumbs-up" size={14} color={colors.success} />
            )}
            {item.accepted === false && (
              <Ionicons name="thumbs-down" size={14} color={colors.error} />
            )}
          </View>
          <Text style={styles.rationale} numberOfLines={2}>{item.rationale}</Text>
          <View style={styles.cardMeta}>
            <Text style={styles.date}>{date}</Text>
            {item.season && <Text style={styles.season}>{item.season}</Text>}
          </View>
        </View>
        <Ionicons name="chevron-forward" size={16} color={colors.border} />
      </TouchableOpacity>
    );
  };

  return (
    <FlatList
      data={history}
      keyExtractor={(item) => String(item.id)}
      renderItem={renderItem}
      contentContainerStyle={styles.list}
      style={{ backgroundColor: colors.background }}
    />
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background, padding: spacing.xl },
  errorText: { ...typography.body, color: colors.error, marginTop: spacing.md, textAlign: 'center' },
  emptyTitle: { ...typography.h3, marginTop: spacing.lg },
  emptySubtitle: { ...typography.body, color: colors.textMuted, textAlign: 'center', marginTop: spacing.sm },
  list: { padding: spacing.lg, paddingBottom: spacing.xxl },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: radius.xl,
    padding: spacing.md,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    gap: spacing.md,
  },
  cardIcon: {
    width: 44,
    height: 44,
    borderRadius: radius.lg,
    backgroundColor: `${colors.primary}18`,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardBody: { flex: 1 },
  cardTop: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginBottom: 2 },
  occasion: { ...typography.body, fontWeight: '600', textTransform: 'capitalize' },
  rationale: { ...typography.caption, color: colors.textMuted, lineHeight: 18, marginBottom: spacing.xs },
  cardMeta: { flexDirection: 'row', gap: spacing.md },
  date: { ...typography.caption, color: colors.border },
  season: { ...typography.caption, color: colors.primary, textTransform: 'capitalize' },
});
