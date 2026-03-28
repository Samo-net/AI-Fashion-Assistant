import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Switch,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import auth from '@react-native-firebase/auth';
import { colors, spacing, typography, radius } from '@/theme';
import { Button } from '@/components/Button';
import { useAuthStore } from '@/store/authStore';

const ROW_ITEMS = [
  { icon: 'person-outline', label: 'Body Type', field: 'body_type' },
  { icon: 'color-palette-outline', label: 'Skin Tone', field: 'skin_tone' },
  { icon: 'heart-outline', label: 'Style Preference', field: 'style_preference' },
  { icon: 'location-outline', label: 'City', field: 'city' },
];

export default function ProfileScreen() {
  const { user, setUser } = useAuthStore();
  const [signingOut, setSigningOut] = useState(false);

  const handleSignOut = async () => {
    Alert.alert('Sign Out', 'Are you sure you want to sign out?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Sign Out',
        style: 'destructive',
        onPress: async () => {
          setSigningOut(true);
          try {
            await auth().signOut();
            setUser(null);
          } catch {
            Alert.alert('Error', 'Failed to sign out. Please try again.');
          } finally {
            setSigningOut(false);
          }
        },
      },
    ]);
  };

  const handleDeleteData = () => {
    Alert.alert(
      'Delete All My Data',
      'This will permanently delete your wardrobe, recommendations, and analytics data. This cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            // TODO: call DELETE /users/{id} endpoint
            Alert.alert('Requested', 'Your data deletion request has been submitted.');
          },
        },
      ]
    );
  };

  if (!user) return null;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Avatar */}
      <View style={styles.avatarSection}>
        <View style={styles.avatarCircle}>
          <Ionicons name="person" size={44} color={colors.primary} />
        </View>
        <Text style={styles.displayName}>{user.display_name ?? 'Fashion Star'}</Text>
        <Text style={styles.email}>{user.email}</Text>
      </View>

      {/* Profile Details */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Profile Details</Text>
        {ROW_ITEMS.map(({ icon, label, field }) => (
          <View key={field} style={styles.row}>
            <Ionicons name={icon as any} size={20} color={colors.textMuted} style={styles.rowIcon} />
            <Text style={styles.rowLabel}>{label}</Text>
            <Text style={styles.rowValue}>
              {(user as any)[field] ?? <Text style={styles.rowEmpty}>Not set</Text>}
            </Text>
          </View>
        ))}
      </View>

      {/* Privacy */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Privacy & Data</Text>
        <View style={styles.row}>
          <Ionicons name="shield-checkmark-outline" size={20} color={colors.success} style={styles.rowIcon} />
          <Text style={styles.rowLabel}>GDPR / NDPR Consent</Text>
          <Switch
            value={user.gdpr_consent ?? false}
            disabled
            trackColor={{ true: colors.success }}
          />
        </View>
        <TouchableOpacity style={styles.row} onPress={handleDeleteData}>
          <Ionicons name="trash-outline" size={20} color={colors.error} style={styles.rowIcon} />
          <Text style={[styles.rowLabel, { color: colors.error }]}>Delete All My Data</Text>
          <Ionicons name="chevron-forward" size={16} color={colors.error} />
        </TouchableOpacity>
      </View>

      {/* Sign Out */}
      <Button
        title="Sign Out"
        onPress={handleSignOut}
        loading={signingOut}
        variant="outline"
        style={styles.signOutBtn}
      />

      <Text style={styles.version}>AI Fashion Assistant v1.0.0 · Veritas University</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: spacing.lg, paddingBottom: spacing.xxl },
  avatarSection: { alignItems: 'center', marginBottom: spacing.xl },
  avatarCircle: {
    width: 90,
    height: 90,
    borderRadius: radius.full,
    backgroundColor: colors.surfaceLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
    borderWidth: 2,
    borderColor: colors.primary,
  },
  displayName: { ...typography.h2, marginBottom: 4 },
  email: { ...typography.caption, color: colors.textMuted },
  section: {
    backgroundColor: colors.surface,
    borderRadius: radius.xl,
    paddingHorizontal: spacing.md,
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },
  sectionTitle: {
    ...typography.caption,
    color: colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 1,
    paddingTop: spacing.md,
    paddingBottom: spacing.sm,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  rowIcon: { marginRight: spacing.md },
  rowLabel: { ...typography.body, flex: 1 },
  rowValue: { ...typography.body, color: colors.textMuted, textTransform: 'capitalize' },
  rowEmpty: { color: colors.border, fontStyle: 'italic' },
  signOutBtn: { marginBottom: spacing.md },
  version: { ...typography.caption, color: colors.border, textAlign: 'center' },
});
