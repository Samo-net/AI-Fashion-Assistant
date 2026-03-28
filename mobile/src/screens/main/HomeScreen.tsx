import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, typography, radius } from '@/theme';
import { Button } from '@/components/Button';
import { useAuthStore } from '@/store/authStore';
import { recommendationsApi, Recommendation } from '@/api/recommendations';
import { getErrorMessage } from '@/api/client';

const OCCASIONS = [
  { label: 'Casual', value: 'casual', emoji: '😊' },
  { label: 'Work', value: 'work', emoji: '💼' },
  { label: 'Church', value: 'church', emoji: '⛪' },
  { label: 'Wedding', value: 'wedding-guest', emoji: '💒' },
  { label: 'Traditional', value: 'traditional-ceremony', emoji: '🥁' },
  { label: 'Date', value: 'date', emoji: '❤️' },
];

export default function HomeScreen() {
  const navigation = useNavigation<any>();
  const { user } = useAuthStore();

  const [selectedOccasion, setSelectedOccasion] = useState('casual');
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [loading, setLoading] = useState(false);

  const getRecommendation = async () => {
    setLoading(true);
    try {
      const rec = await recommendationsApi.create(selectedOccasion);
      setRecommendation(rec);
    } catch (e) {
      Alert.alert('Recommendation Failed', getErrorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  const submitFeedback = async (accepted: boolean) => {
    if (!recommendation) return;
    try {
      await recommendationsApi.submitFeedback(recommendation.id, { accepted });
      setRecommendation((r) => r ? { ...r, accepted } : r);
    } catch {
      // Non-critical
    }
  };

  const greeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>{greeting()},</Text>
          <Text style={styles.name}>{user?.display_name?.split(' ')[0] ?? 'Fashion Star'} 👋</Text>
        </View>
        <TouchableOpacity onPress={() => navigation.navigate('Profile')}>
          <View style={styles.avatar}>
            <Ionicons name="person" size={22} color={colors.primary} />
          </View>
        </TouchableOpacity>
      </View>

      {/* Occasion Selector */}
      <Text style={styles.sectionTitle}>What's the occasion?</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.occasionRow}>
        {OCCASIONS.map((o) => (
          <TouchableOpacity
            key={o.value}
            style={[styles.occasionChip, selectedOccasion === o.value && styles.occasionSelected]}
            onPress={() => setSelectedOccasion(o.value)}
          >
            <Text style={styles.occasionEmoji}>{o.emoji}</Text>
            <Text style={[styles.occasionLabel, selectedOccasion === o.value && styles.occasionLabelSelected]}>
              {o.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <Button
        title="Get Outfit Suggestion"
        onPress={getRecommendation}
        loading={loading}
        style={styles.btn}
      />

      {/* Recommendation Card */}
      {recommendation && (
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Today's Outfit ✨</Text>
            {recommendation.season && (
              <Text style={styles.badge}>{recommendation.season}</Text>
            )}
          </View>

          {recommendation.weather_condition && (
            <Text style={styles.weather}>
              🌤 {Math.round(recommendation.weather_temp_celsius ?? 0)}°C · {recommendation.weather_condition}
            </Text>
          )}

          <Text style={styles.rationale}>{recommendation.rationale}</Text>

          {recommendation.accessory_suggestion && (
            <View style={styles.accessory}>
              <Ionicons name="sparkles" size={14} color={colors.secondary} />
              <Text style={styles.accessoryText}> {recommendation.accessory_suggestion}</Text>
            </View>
          )}

          {/* Action row */}
          <View style={styles.actionRow}>
            <TouchableOpacity
              style={[styles.actionBtn, recommendation.accepted === true && styles.actionBtnActive]}
              onPress={() => submitFeedback(true)}
            >
              <Ionicons name="thumbs-up" size={18} color={recommendation.accepted === true ? colors.white : colors.textMuted} />
              <Text style={[styles.actionText, recommendation.accepted === true && styles.actionTextActive]}>Love it</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.actionBtn, recommendation.accepted === false && styles.actionBtnReject]}
              onPress={() => submitFeedback(false)}
            >
              <Ionicons name="thumbs-down" size={18} color={recommendation.accepted === false ? colors.white : colors.textMuted} />
              <Text style={[styles.actionText, recommendation.accepted === false && styles.actionTextActive]}>Not for me</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionBtn}
              onPress={() => navigation.navigate('Visualization', { recommendationId: recommendation.id })}
            >
              <Ionicons name="image" size={18} color={colors.primary} />
              <Text style={[styles.actionText, { color: colors.primary }]}>Visualise</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Quick Links */}
      <View style={styles.quickLinks}>
        <TouchableOpacity style={styles.quickCard} onPress={() => navigation.navigate('Wardrobe')}>
          <Ionicons name="shirt" size={28} color={colors.primary} />
          <Text style={styles.quickLabel}>My Wardrobe</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.quickCard} onPress={() => navigation.navigate('Analytics')}>
          <Ionicons name="leaf" size={28} color={colors.success} />
          <Text style={styles.quickLabel}>Sustainability</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.quickCard} onPress={() => navigation.navigate('History')}>
          <Ionicons name="time" size={28} color={colors.secondary} />
          <Text style={styles.quickLabel}>History</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: spacing.lg, paddingBottom: spacing.xxl },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.xl },
  greeting: { ...typography.body, color: colors.textMuted },
  name: { ...typography.h2 },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: radius.full,
    backgroundColor: colors.surfaceLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sectionTitle: { ...typography.h3, marginBottom: spacing.md },
  occasionRow: { marginBottom: spacing.lg },
  occasionChip: {
    alignItems: 'center',
    padding: spacing.md,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    marginRight: spacing.sm,
    minWidth: 72,
    borderWidth: 1,
    borderColor: colors.border,
  },
  occasionSelected: { backgroundColor: colors.primary, borderColor: colors.primary },
  occasionEmoji: { fontSize: 24, marginBottom: spacing.xs },
  occasionLabel: { ...typography.caption, color: colors.textMuted },
  occasionLabelSelected: { color: colors.white, fontWeight: '600' },
  btn: { marginBottom: spacing.xl },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.xl,
    padding: spacing.lg,
    marginBottom: spacing.xl,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.sm },
  cardTitle: { ...typography.h3 },
  badge: {
    ...typography.caption,
    color: colors.primary,
    backgroundColor: `${colors.primary}22`,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radius.full,
    textTransform: 'capitalize',
  },
  weather: { ...typography.caption, color: colors.textMuted, marginBottom: spacing.md },
  rationale: { ...typography.body, lineHeight: 22, marginBottom: spacing.md },
  accessory: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.md },
  accessoryText: { ...typography.caption, color: colors.secondary, flex: 1 },
  actionRow: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.sm },
  actionBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    paddingVertical: spacing.sm,
    borderRadius: radius.md,
    backgroundColor: colors.surfaceLight,
    borderWidth: 1,
    borderColor: colors.border,
  },
  actionBtnActive: { backgroundColor: colors.success, borderColor: colors.success },
  actionBtnReject: { backgroundColor: colors.error, borderColor: colors.error },
  actionText: { ...typography.caption, color: colors.textMuted },
  actionTextActive: { color: colors.white },
  quickLinks: { flexDirection: 'row', gap: spacing.sm },
  quickCard: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: spacing.md,
    alignItems: 'center',
    gap: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  quickLabel: { ...typography.caption, textAlign: 'center' },
});
