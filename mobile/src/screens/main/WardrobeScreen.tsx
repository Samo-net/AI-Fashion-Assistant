import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Image,
  TextInput,
  ActivityIndicator,
  Alert,
  RefreshControl,
} from 'react-native';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, typography, radius } from '@/theme';
import { useWardrobeStore } from '@/store/wardrobeStore';
import { WardrobeItem } from '@/api/wardrobe';

const CATEGORIES = [
  { label: 'All', value: '' },
  { label: 'Tops', value: 'tops' },
  { label: 'Bottoms', value: 'bottoms' },
  { label: 'Ankara', value: 'ankara' },
  { label: 'Agbada', value: 'agbada' },
  { label: 'Kaftan', value: 'kaftan' },
  { label: 'Dress', value: 'dress' },
  { label: 'Footwear', value: 'footwear' },
  { label: 'Accessories', value: 'accessories' },
];

function ItemCard({ item, onPress }: { item: WardrobeItem; onPress: () => void }) {
  return (
    <TouchableOpacity style={styles.itemCard} onPress={onPress} activeOpacity={0.85}>
      {item.image_url ? (
        <Image source={{ uri: item.image_url }} style={styles.itemImage} resizeMode="cover" />
      ) : (
        <View style={[styles.itemImage, styles.imagePlaceholder]}>
          <Ionicons name="shirt" size={32} color={colors.textMuted} />
        </View>
      )}
      {!item.clip_processed && (
        <View style={styles.processingBadge}>
          <ActivityIndicator size="small" color={colors.primary} />
        </View>
      )}
      <View style={styles.itemInfo}>
        <Text style={styles.itemName} numberOfLines={1}>{item.name}</Text>
        <Text style={styles.itemMeta}>
          {item.primary_color ? `${item.primary_color} · ` : ''}{item.category}
        </Text>
      </View>
    </TouchableOpacity>
  );
}

export default function WardrobeScreen() {
  const navigation = useNavigation<any>();
  const { items, loading, fetchItems, search } = useWardrobeStore();

  const [activeCategory, setActiveCategory] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<WardrobeItem[] | null>(null);
  const [searching, setSearching] = useState(false);

  useFocusEffect(
    useCallback(() => {
      fetchItems(activeCategory || undefined);
    }, [activeCategory])
  );

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    setSearching(true);
    const results = await search(searchQuery.trim());
    setSearchResults(results);
    setSearching(false);
  };

  const displayItems = searchResults ?? items;

  return (
    <View style={styles.container}>
      {/* Search bar */}
      <View style={styles.searchRow}>
        <View style={styles.searchBox}>
          <Ionicons name="search" size={18} color={colors.textMuted} style={styles.searchIcon} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search your wardrobe..."
            placeholderTextColor={colors.textMuted}
            value={searchQuery}
            onChangeText={(t) => {
              setSearchQuery(t);
              if (!t) setSearchResults(null);
            }}
            onSubmitEditing={handleSearch}
            returnKeyType="search"
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => { setSearchQuery(''); setSearchResults(null); }}>
              <Ionicons name="close-circle" size={18} color={colors.textMuted} />
            </TouchableOpacity>
          )}
        </View>
        <TouchableOpacity style={styles.addBtn} onPress={() => navigation.navigate('AddItem')}>
          <Ionicons name="add" size={24} color={colors.white} />
        </TouchableOpacity>
      </View>

      {/* Category filter */}
      {!searchResults && (
        <FlatList
          data={CATEGORIES}
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.catList}
          keyExtractor={(i) => i.value}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={[styles.catChip, activeCategory === item.value && styles.catChipActive]}
              onPress={() => setActiveCategory(item.value)}
            >
              <Text style={[styles.catLabel, activeCategory === item.value && styles.catLabelActive]}>
                {item.label}
              </Text>
            </TouchableOpacity>
          )}
        />
      )}

      {/* Items grid */}
      {loading || searching ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.primary} size="large" />
        </View>
      ) : displayItems.length === 0 ? (
        <View style={styles.center}>
          <Ionicons name="shirt-outline" size={64} color={colors.border} />
          <Text style={styles.emptyTitle}>
            {searchResults ? 'No results found' : 'Your wardrobe is empty'}
          </Text>
          <Text style={styles.emptyBody}>
            {searchResults
              ? 'Try a different search term'
              : 'Tap + to add your first clothing item'}
          </Text>
        </View>
      ) : (
        <FlatList
          data={displayItems}
          numColumns={2}
          keyExtractor={(i) => String(i.id)}
          contentContainerStyle={styles.grid}
          refreshControl={
            <RefreshControl
              refreshing={loading}
              onRefresh={() => fetchItems(activeCategory || undefined)}
              tintColor={colors.primary}
            />
          }
          renderItem={({ item }) => (
            <ItemCard
              item={item}
              onPress={() => navigation.navigate('ItemDetail', { itemId: item.id })}
            />
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  searchRow: { flexDirection: 'row', padding: spacing.lg, gap: spacing.sm, alignItems: 'center' },
  searchBox: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing.md,
  },
  searchIcon: { marginRight: spacing.sm },
  searchInput: { flex: 1, ...typography.body, paddingVertical: spacing.sm, color: colors.text },
  addBtn: {
    width: 44,
    height: 44,
    borderRadius: radius.md,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  catList: { paddingHorizontal: spacing.lg, paddingBottom: spacing.md, gap: spacing.sm },
  catChip: {
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.md,
    borderRadius: radius.full,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  catChipActive: { backgroundColor: colors.primary, borderColor: colors.primary },
  catLabel: { ...typography.caption, color: colors.textMuted },
  catLabelActive: { color: colors.white, fontWeight: '600' },
  grid: { paddingHorizontal: spacing.md, paddingBottom: spacing.xxl },
  itemCard: {
    flex: 1,
    margin: spacing.xs,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: colors.border,
  },
  itemImage: { width: '100%', aspectRatio: 1 },
  imagePlaceholder: { backgroundColor: colors.surfaceLight, alignItems: 'center', justifyContent: 'center' },
  processingBadge: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: `${colors.surface}cc`,
    borderRadius: radius.full,
    padding: 4,
  },
  itemInfo: { padding: spacing.sm },
  itemName: { ...typography.body, fontSize: 13, fontWeight: '600' },
  itemMeta: { ...typography.caption, marginTop: 2, textTransform: 'capitalize' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: spacing.md },
  emptyTitle: { ...typography.h3, color: colors.textMuted },
  emptyBody: { ...typography.body, color: colors.textMuted, textAlign: 'center' },
});
