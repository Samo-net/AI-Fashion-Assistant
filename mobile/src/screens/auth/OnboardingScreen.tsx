import React, { useRef, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  Dimensions,
  TouchableOpacity,
  Image,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { colors, spacing, typography, radius } from '@/theme';
import { Button } from '@/components/Button';

const { width } = Dimensions.get('window');

const SLIDES = [
  {
    id: '1',
    title: 'Your Smart Wardrobe',
    body: 'Upload your clothing items and let AI organise, tag, and search your wardrobe instantly.',
    emoji: '👗',
  },
  {
    id: '2',
    title: 'AI Outfit Suggestions',
    body: 'Get personalised outfit recommendations based on your occasion, weather, and Nigerian style preferences.',
    emoji: '✨',
  },
  {
    id: '3',
    title: 'Visualise Your Look',
    body: 'See your outfits come to life with AI-generated 2D fashion visuals tailored to your skin tone.',
    emoji: '🎨',
  },
  {
    id: '4',
    title: 'Dress Sustainably',
    body: 'Track what you wear, discover unworn items, and build conscious fashion habits.',
    emoji: '🌿',
  },
];

export default function OnboardingScreen() {
  const navigation = useNavigation<any>();
  const listRef = useRef<FlatList>(null);
  const [activeIndex, setActiveIndex] = useState(0);

  const goNext = () => {
    if (activeIndex < SLIDES.length - 1) {
      listRef.current?.scrollToIndex({ index: activeIndex + 1 });
      setActiveIndex((i) => i + 1);
    } else {
      navigation.replace('Login');
    }
  };

  return (
    <View style={styles.container}>
      <FlatList
        ref={listRef}
        data={SLIDES}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={(e) => {
          const idx = Math.round(e.nativeEvent.contentOffset.x / width);
          setActiveIndex(idx);
        }}
        renderItem={({ item }) => (
          <View style={styles.slide}>
            <Text style={styles.emoji}>{item.emoji}</Text>
            <Text style={styles.title}>{item.title}</Text>
            <Text style={styles.body}>{item.body}</Text>
          </View>
        )}
        keyExtractor={(item) => item.id}
      />

      {/* Dots */}
      <View style={styles.dots}>
        {SLIDES.map((_, i) => (
          <View key={i} style={[styles.dot, i === activeIndex && styles.dotActive]} />
        ))}
      </View>

      <View style={styles.actions}>
        <Button
          title={activeIndex === SLIDES.length - 1 ? 'Get Started' : 'Next'}
          onPress={goNext}
          style={styles.btn}
        />
        {activeIndex < SLIDES.length - 1 && (
          <TouchableOpacity onPress={() => navigation.replace('Login')}>
            <Text style={styles.skip}>Skip</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  slide: {
    width,
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
  },
  emoji: { fontSize: 80, marginBottom: spacing.xl },
  title: { ...typography.h1, textAlign: 'center', marginBottom: spacing.md },
  body: { ...typography.body, textAlign: 'center', color: colors.textMuted, lineHeight: 24 },
  dots: { flexDirection: 'row', justifyContent: 'center', marginBottom: spacing.lg },
  dot: {
    width: 8,
    height: 8,
    borderRadius: radius.full,
    backgroundColor: colors.border,
    marginHorizontal: 4,
  },
  dotActive: { backgroundColor: colors.primary, width: 24 },
  actions: { paddingHorizontal: spacing.xl, paddingBottom: spacing.xxl, alignItems: 'center' },
  btn: { width: '100%', marginBottom: spacing.md },
  skip: { ...typography.body, color: colors.textMuted },
});
