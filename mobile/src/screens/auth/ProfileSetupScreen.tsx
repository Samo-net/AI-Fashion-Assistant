import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { colors, spacing, typography, radius } from '@/theme';
import { Button } from '@/components/Button';
import { Input } from '@/components/Input';
import { useAuthStore } from '@/store/authStore';

const BODY_TYPES = ['Slim', 'Athletic', 'Average', 'Curvy', 'Plus-size', 'Petite'];
const SKIN_TONES = ['Deep Brown', 'Dark Brown', 'Medium Brown', 'Caramel', 'Warm Brown', 'Light Brown'];
const STYLES = ['Casual', 'Traditional', 'Formal', 'Smart-casual', 'Mix'];
const CITIES = ['Abuja', 'Lagos', 'Port Harcourt', 'Kano', 'Ibadan', 'Enugu', 'Benin City', 'Other'];

function OptionGrid({
  label,
  options,
  selected,
  onSelect,
}: {
  label: string;
  options: string[];
  selected: string;
  onSelect: (v: string) => void;
}) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionLabel}>{label}</Text>
      <View style={styles.grid}>
        {options.map((opt) => (
          <TouchableOpacity
            key={opt}
            style={[styles.chip, selected === opt && styles.chipSelected]}
            onPress={() => onSelect(opt)}
          >
            <Text style={[styles.chipText, selected === opt && styles.chipTextSelected]}>
              {opt}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}

export default function ProfileSetupScreen() {
  const navigation = useNavigation<any>();
  const { updateProfile, loading } = useAuthStore();

  const [bodyType, setBodyType] = useState('');
  const [skinTone, setSkinTone] = useState('');
  const [stylePreference, setStylePreference] = useState('');
  const [city, setCity] = useState('');

  const handleSave = async () => {
    if (!bodyType || !skinTone || !city) {
      Alert.alert('Almost there!', 'Please select your body type, skin tone, and city.');
      return;
    }
    try {
      await updateProfile({
        body_type: bodyType.toLowerCase(),
        skin_tone: skinTone.toLowerCase(),
        style_preference: stylePreference.toLowerCase() || 'mix',
        city,
      });
      navigation.replace('MainTabs');
    } catch {
      Alert.alert('Error', 'Could not save profile. Please try again.');
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Set Up Your Profile</Text>
      <Text style={styles.subtitle}>
        This helps us personalise outfit recommendations just for you.
      </Text>

      <OptionGrid label="Body Type" options={BODY_TYPES} selected={bodyType} onSelect={setBodyType} />
      <OptionGrid label="Skin Tone" options={SKIN_TONES} selected={skinTone} onSelect={setSkinTone} />
      <OptionGrid label="Style Preference" options={STYLES} selected={stylePreference} onSelect={setStylePreference} />
      <OptionGrid label="Your City" options={CITIES} selected={city} onSelect={setCity} />

      <Button
        title="Start Using My Wardrobe"
        onPress={handleSave}
        loading={loading}
        style={styles.btn}
      />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: spacing.xl, paddingBottom: spacing.xxl },
  title: { ...typography.h1, marginBottom: spacing.xs, marginTop: spacing.xl },
  subtitle: { ...typography.body, color: colors.textMuted, marginBottom: spacing.xl, lineHeight: 22 },
  section: { marginBottom: spacing.xl },
  sectionLabel: { ...typography.h3, marginBottom: spacing.md },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  chip: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: radius.full,
    backgroundColor: colors.surfaceLight,
    borderWidth: 1,
    borderColor: colors.border,
  },
  chipSelected: { backgroundColor: colors.primary, borderColor: colors.primary },
  chipText: { ...typography.body, color: colors.textMuted },
  chipTextSelected: { color: colors.white, fontWeight: '600' },
  btn: { marginTop: spacing.md },
});
