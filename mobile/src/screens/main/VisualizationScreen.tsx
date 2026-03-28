import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  Image,
  TouchableOpacity,
  Alert,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, typography, radius } from '@/theme';
import { Button } from '@/components/Button';
import { apiClient, getErrorMessage } from '@/api/client';

type JobStatus = 'queued' | 'processing' | 'done' | 'failed';

interface VisualizationJob {
  id: string;
  status: JobStatus;
  image_url?: string;
  error_message?: string;
}

export default function VisualizationScreen({ route, navigation }: any) {
  const { recommendationId } = route.params as { recommendationId: number };

  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<VisualizationJob | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const startVisualization = async () => {
    setSubmitting(true);
    try {
      const res = await apiClient.post('/visualizations', { recommendation_id: recommendationId });
      setJobId(res.data.id);
      setJob(res.data);
    } catch (e) {
      Alert.alert('Error', getErrorMessage(e));
    } finally {
      setSubmitting(false);
    }
  };

  const pollJob = useCallback(async () => {
    if (!jobId) return;
    try {
      const res = await apiClient.get(`/visualizations/${jobId}`);
      setJob(res.data);
    } catch {
      // Silently ignore poll errors
    }
  }, [jobId]);

  useEffect(() => {
    if (!jobId || job?.status === 'done' || job?.status === 'failed') return;
    const interval = setInterval(pollJob, 3000);
    return () => clearInterval(interval);
  }, [jobId, job?.status, pollJob]);

  const statusLabel: Record<JobStatus, string> = {
    queued: 'Queued — waiting for GPU...',
    processing: 'Generating your outfit visualization...',
    done: 'Done!',
    failed: 'Generation failed',
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Outfit Visualization</Text>
      <Text style={styles.subtitle}>
        AI generates a 2D preview of your recommended outfit using Stable Diffusion + ControlNet.
      </Text>

      {!jobId && (
        <Button
          title="Generate Visualization"
          onPress={startVisualization}
          loading={submitting}
          style={styles.btn}
        />
      )}

      {job && job.status !== 'done' && job.status !== 'failed' && (
        <View style={styles.statusCard}>
          <ActivityIndicator color={colors.primary} size="large" style={{ marginBottom: spacing.md }} />
          <Text style={styles.statusText}>{statusLabel[job.status]}</Text>
          <Text style={styles.statusHint}>This typically takes 20–40 seconds.</Text>
        </View>
      )}

      {job?.status === 'done' && job.image_url && (
        <View style={styles.resultCard}>
          <Image
            source={{ uri: job.image_url }}
            style={styles.resultImage}
            resizeMode="contain"
          />
          <View style={styles.resultActions}>
            <TouchableOpacity style={styles.resultBtn} onPress={startVisualization}>
              <Ionicons name="refresh" size={18} color={colors.primary} />
              <Text style={[styles.resultBtnText, { color: colors.primary }]}>Regenerate</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {job?.status === 'failed' && (
        <View style={styles.errorCard}>
          <Ionicons name="warning-outline" size={32} color={colors.error} />
          <Text style={styles.errorText}>{job.error_message ?? 'Visualization failed. Please try again.'}</Text>
          <Button title="Try Again" onPress={startVisualization} loading={submitting} style={{ marginTop: spacing.md }} />
        </View>
      )}

      <View style={styles.disclaimer}>
        <Ionicons name="information-circle-outline" size={14} color={colors.textMuted} />
        <Text style={styles.disclaimerText}>
          {' '}AI-generated image. Results are illustrative and may not perfectly represent the actual garments.
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: spacing.lg, paddingBottom: spacing.xxl },
  title: { ...typography.h2, marginBottom: spacing.sm },
  subtitle: { ...typography.body, color: colors.textMuted, marginBottom: spacing.xl, lineHeight: 22 },
  btn: { marginBottom: spacing.xl },
  statusCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.xl,
    padding: spacing.xl,
    alignItems: 'center',
    marginBottom: spacing.xl,
    borderWidth: 1,
    borderColor: colors.border,
  },
  statusText: { ...typography.body, fontWeight: '600', textAlign: 'center' },
  statusHint: { ...typography.caption, color: colors.textMuted, marginTop: spacing.sm, textAlign: 'center' },
  resultCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.xl,
    overflow: 'hidden',
    marginBottom: spacing.xl,
    borderWidth: 1,
    borderColor: colors.border,
  },
  resultImage: { width: '100%', aspectRatio: 1 },
  resultActions: { flexDirection: 'row', justifyContent: 'center', padding: spacing.md },
  resultBtn: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  resultBtnText: { ...typography.body, fontWeight: '600' },
  errorCard: {
    backgroundColor: `${colors.error}15`,
    borderRadius: radius.xl,
    padding: spacing.xl,
    alignItems: 'center',
    marginBottom: spacing.xl,
    borderWidth: 1,
    borderColor: `${colors.error}40`,
  },
  errorText: { ...typography.body, color: colors.error, textAlign: 'center', marginTop: spacing.sm },
  disclaimer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: colors.surfaceLight,
    borderRadius: radius.md,
    padding: spacing.md,
  },
  disclaimerText: { ...typography.caption, color: colors.textMuted, flex: 1, lineHeight: 18 },
});
