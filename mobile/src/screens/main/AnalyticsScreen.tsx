import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, typography, radius } from '@/theme';
import { recommendationsApi, WardrobeSummary } from '@/api/recommendations';

function ScoreRing({ score }: { score: number }) {
  const color = score >= 70 ? colors.success : score >= 40 ? colors.warning : colors.error;
  return (
    <View style={[styles.scoreRing, { borderColor: color }]}>
      <Text style={[styles.scoreNumber, { color }]}>{score}</Text>
      <Text style={styles.scoreLabel}>/ 100</Text>
    </View>
  );
}

function StatCard({ icon, label, value, sub }: { icon: string; label: string; value: string; sub?: string }) {
  return (
    <View style={styles.statCard}>
      <Ionicons name={icon as any} size={22} color={colors.primary} />
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
      {sub && <Text style={styles.statSub}>{sub}</Text>}
    </View>
  );
}

export default function AnalyticsScreen() {
  const [summary, setSummary] = useState<WardrobeSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [unwornDays, setUnwornDays] = useState(30);
  const [unwornItems, setUnwornItems] = useState<any[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadUnworn();
  }, [unwornDays]);

  const loadData = async () => {
    setLoading(true);
    try {
      const s = await recommendationsApi.getAnalyticsSummary();
      setSummary(s);
    } finally {
      setLoading(false);
    }
  };

  const loadUnworn = async () => {
    const items = await recommendationsApi.getUnwornItems(unwornDays);
    setUnwornItems(items);
  };

  if (loading || !summary) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.primary} size="large" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Sustainability Dashboard</Text>
      <Text style={styles.subtitle}>Track how consciously you use your wardrobe.</Text>

      {/* Score ring */}
      <View style={styles.scoreSection}>
        <ScoreRing score={summary.sustainability_score} />
        <View style={styles.scoreInfo}>
          <Text style={styles.scoreTitle}>Sustainability Score</Text>
          <Text style={styles.scoreDesc}>
            Based on how much of your wardrobe you actively wear.
          </Text>
        </View>
      </View>

      {/* Stat grid */}
      <View style={styles.statGrid}>
        <StatCard
          icon="shirt"
          label="Total Items"
          value={String(summary.total_items)}
        />
        <StatCard
          icon="checkmark-circle"
          label="Items Worn"
          value={String(summary.items_worn_at_least_once)}
          sub={`${Math.round(summary.utilization_rate * 100)}% utilisation`}
        />
        <StatCard
          icon="alert-circle"
          label="Unworn (30d)"
          value={String(summary.unworn_30_days)}
        />
        <StatCard
          icon="time"
          label="Unworn (90d)"
          value={String(summary.unworn_90_days)}
        />
      </View>

      {/* Most worn */}
      <Text style={styles.sectionTitle}>Most Worn Items</Text>
      {summary.item_stats.slice(0, 5).map((s) => (
        <View key={s.item_id} style={styles.itemRow}>
          <View style={styles.itemRowLeft}>
            <Text style={styles.itemRowName} numberOfLines={1}>{s.item_name}</Text>
            <Text style={styles.itemRowMeta}>{s.category}</Text>
          </View>
          <View style={styles.itemRowRight}>
            <Text style={styles.wearCount}>{s.wear_count}×</Text>
            {s.cost_per_wear != null && (
              <Text style={styles.cpw}>₦{s.cost_per_wear.toLocaleString()} / wear</Text>
            )}
          </View>
        </View>
      ))}

      {/* Unworn items filter */}
      <View style={styles.unwornHeader}>
        <Text style={styles.sectionTitle}>Unworn Items</Text>
        <View style={styles.daysRow}>
          {[30, 60, 90].map((d) => (
            <TouchableOpacity
              key={d}
              style={[styles.dayChip, unwornDays === d && styles.dayChipActive]}
              onPress={() => setUnwornDays(d)}
            >
              <Text style={[styles.dayText, unwornDays === d && styles.dayTextActive]}>{d}d</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {unwornItems.length === 0 ? (
        <View style={styles.emptyUnworn}>
          <Ionicons name="checkmark-circle" size={32} color={colors.success} />
          <Text style={styles.emptyText}>All items worn recently!</Text>
        </View>
      ) : (
        unwornItems.map((item: any) => (
          <View key={item.item_id} style={styles.unwornCard}>
            <Ionicons name="shirt-outline" size={18} color={colors.textMuted} />
            <View style={styles.unwornInfo}>
              <Text style={styles.unwornName}>{item.item_name}</Text>
              <Text style={styles.unwornMeta}>{item.category}</Text>
            </View>
            <Text style={styles.unwornTag}>Not worn</Text>
          </View>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: spacing.lg, paddingBottom: spacing.xxl },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  title: { ...typography.h2, marginBottom: spacing.xs },
  subtitle: { ...typography.body, color: colors.textMuted, marginBottom: spacing.xl },
  scoreSection: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: radius.xl,
    padding: spacing.lg,
    marginBottom: spacing.xl,
    borderWidth: 1,
    borderColor: colors.border,
    gap: spacing.lg,
  },
  scoreRing: {
    width: 80,
    height: 80,
    borderRadius: 40,
    borderWidth: 4,
    alignItems: 'center',
    justifyContent: 'center',
  },
  scoreNumber: { fontSize: 22, fontWeight: '700' },
  scoreLabel: { ...typography.caption, color: colors.textMuted },
  scoreInfo: { flex: 1 },
  scoreTitle: { ...typography.h3, marginBottom: spacing.xs },
  scoreDesc: { ...typography.caption, lineHeight: 18 },
  statGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginBottom: spacing.xl },
  statCard: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: spacing.md,
    alignItems: 'center',
    gap: spacing.xs,
    borderWidth: 1,
    borderColor: colors.border,
  },
  statValue: { ...typography.h2 },
  statLabel: { ...typography.caption, textAlign: 'center' },
  statSub: { ...typography.caption, color: colors.primary, textAlign: 'center' },
  sectionTitle: { ...typography.h3, marginBottom: spacing.md },
  itemRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  itemRowLeft: { flex: 1 },
  itemRowName: { ...typography.body, fontWeight: '600' },
  itemRowMeta: { ...typography.caption, textTransform: 'capitalize' },
  itemRowRight: { alignItems: 'flex-end' },
  wearCount: { ...typography.h3, color: colors.primary },
  cpw: { ...typography.caption, color: colors.textMuted },
  unwornHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.md, marginTop: spacing.md },
  daysRow: { flexDirection: 'row', gap: spacing.xs },
  dayChip: {
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.sm,
    borderRadius: radius.full,
    backgroundColor: colors.surfaceLight,
    borderWidth: 1,
    borderColor: colors.border,
  },
  dayChipActive: { backgroundColor: colors.primary, borderColor: colors.primary },
  dayText: { ...typography.caption, color: colors.textMuted },
  dayTextActive: { color: colors.white },
  emptyUnworn: { alignItems: 'center', padding: spacing.xl, gap: spacing.md },
  emptyText: { ...typography.body, color: colors.success },
  unwornCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  unwornInfo: { flex: 1 },
  unwornName: { ...typography.body, fontWeight: '600' },
  unwornMeta: { ...typography.caption, textTransform: 'capitalize' },
  unwornTag: { ...typography.caption, color: colors.warning },
});
