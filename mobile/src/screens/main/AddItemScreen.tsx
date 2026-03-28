import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import * as ImagePicker from 'expo-image-picker';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, typography, radius } from '@/theme';
import { Button } from '@/components/Button';
import { Input } from '@/components/Input';
import { useWardrobeStore } from '@/store/wardrobeStore';
import { wardrobeApi } from '@/api/wardrobe';
import { getErrorMessage } from '@/api/client';

const CATEGORIES = [
  'tops', 'bottoms', 'dress', 'outerwear', 'footwear', 'accessories',
  'ankara', 'agbada', 'kaftan', 'aso-oke', 'lace', 'senator',
  'iro-and-buba', 'isiagu', 'adire', 'dashiki', 'other',
];

const FORMALITIES = ['casual', 'smart-casual', 'formal', 'traditional'];

export default function AddItemScreen() {
  const navigation = useNavigation<any>();
  const { addItem, loading } = useWardrobeStore();

  const [name, setName] = useState('');
  const [category, setCategory] = useState('');
  const [formality, setFormality] = useState('');
  const [cost, setCost] = useState('');
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [imagePublicUrl, setImagePublicUrl] = useState<string | null>(null);
  const [imageS3Key, setImageS3Key] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const pickImage = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission required', 'Please allow photo access to add clothing items.');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.8,
    });

    if (!result.canceled && result.assets[0]) {
      setImageUri(result.assets[0].uri);
      await uploadImage(result.assets[0].uri);
    }
  };

  const uploadImage = async (uri: string) => {
    setUploading(true);
    try {
      const ext = uri.split('.').pop() ?? 'jpg';
      const { presigned_post, object_key, public_url } = await wardrobeApi.getUploadUrl(ext);

      // Build FormData for S3 presigned POST
      const formData = new FormData();
      const fields = presigned_post.fields as Record<string, string>;
      Object.entries(fields).forEach(([k, v]) => formData.append(k, v));
      formData.append('file', { uri, name: `upload.${ext}`, type: `image/${ext}` } as any);

      await fetch(presigned_post.url as string, { method: 'POST', body: formData });

      setImagePublicUrl(public_url);
      setImageS3Key(object_key);
    } catch (e) {
      Alert.alert('Upload failed', getErrorMessage(e));
      setImageUri(null);
    } finally {
      setUploading(false);
    }
  };

  const validate = () => {
    const e: Record<string, string> = {};
    if (!name.trim()) e.name = 'Item name is required.';
    if (!category) e.category = 'Please select a category.';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleAdd = async () => {
    if (!validate()) return;
    if (uploading) { Alert.alert('Please wait', 'Image is still uploading.'); return; }

    try {
      await addItem({
        name: name.trim(),
        category,
        formality: formality || undefined,
        image_url: imagePublicUrl ?? undefined,
        image_s3_key: imageS3Key ?? undefined,
        purchase_cost: cost ? parseFloat(cost) : undefined,
      });
      navigation.goBack();
    } catch (e) {
      Alert.alert('Failed to add item', getErrorMessage(e));
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      <Text style={styles.title}>Add Clothing Item</Text>

      {/* Image picker */}
      <TouchableOpacity style={styles.imagePicker} onPress={pickImage} disabled={uploading}>
        {imageUri ? (
          <Image source={{ uri: imageUri }} style={styles.previewImage} />
        ) : (
          <View style={styles.imagePlaceholder}>
            <Ionicons name="camera" size={36} color={colors.textMuted} />
            <Text style={styles.imagePrompt}>Tap to add photo</Text>
          </View>
        )}
        {uploading && (
          <View style={styles.uploadOverlay}>
            <ActivityIndicator color={colors.white} />
            <Text style={styles.uploadText}>Uploading...</Text>
          </View>
        )}
      </TouchableOpacity>
      {imagePublicUrl && (
        <Text style={styles.uploadSuccess}>✓ Photo uploaded — AI will auto-tag it</Text>
      )}

      <Input label="Item Name *" value={name} onChangeText={setName} placeholder="e.g. Blue Ankara Top" error={errors.name} />

      {/* Category selector */}
      <Text style={styles.sectionLabel}>Category *</Text>
      {errors.category && <Text style={styles.fieldError}>{errors.category}</Text>}
      <View style={styles.grid}>
        {CATEGORIES.map((cat) => (
          <TouchableOpacity
            key={cat}
            style={[styles.chip, category === cat && styles.chipSelected]}
            onPress={() => setCategory(cat)}
          >
            <Text style={[styles.chipText, category === cat && styles.chipTextSelected]}>
              {cat}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Formality selector */}
      <Text style={styles.sectionLabel}>Formality (optional)</Text>
      <View style={styles.row}>
        {FORMALITIES.map((f) => (
          <TouchableOpacity
            key={f}
            style={[styles.chip, formality === f && styles.chipSelected]}
            onPress={() => setFormality(formality === f ? '' : f)}
          >
            <Text style={[styles.chipText, formality === f && styles.chipTextSelected]}>{f}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <Input
        label="Purchase Cost (₦, optional)"
        value={cost}
        onChangeText={setCost}
        keyboardType="numeric"
        placeholder="e.g. 15000"
      />

      <Button title="Add to Wardrobe" onPress={handleAdd} loading={loading} style={styles.btn} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: spacing.lg, paddingBottom: spacing.xxl },
  title: { ...typography.h2, marginBottom: spacing.xl },
  imagePicker: {
    borderRadius: radius.xl,
    overflow: 'hidden',
    marginBottom: spacing.lg,
    aspectRatio: 1,
    backgroundColor: colors.surface,
    borderWidth: 1.5,
    borderColor: colors.border,
    borderStyle: 'dashed',
  },
  previewImage: { width: '100%', height: '100%' },
  imagePlaceholder: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: spacing.sm },
  imagePrompt: { ...typography.body, color: colors.textMuted },
  uploadOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: `${colors.black}88`,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
  },
  uploadText: { ...typography.body, color: colors.white },
  uploadSuccess: { ...typography.caption, color: colors.success, marginBottom: spacing.md },
  sectionLabel: { ...typography.label, marginBottom: spacing.sm },
  fieldError: { ...typography.caption, color: colors.error, marginBottom: spacing.sm },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginBottom: spacing.lg },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginBottom: spacing.lg },
  chip: {
    paddingVertical: spacing.xs + 2,
    paddingHorizontal: spacing.md,
    borderRadius: radius.full,
    backgroundColor: colors.surfaceLight,
    borderWidth: 1,
    borderColor: colors.border,
  },
  chipSelected: { backgroundColor: colors.primary, borderColor: colors.primary },
  chipText: { ...typography.caption, color: colors.textMuted, textTransform: 'capitalize' },
  chipTextSelected: { color: colors.white, fontWeight: '600' },
  btn: { marginTop: spacing.md },
});
