import React, { useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { ActivityIndicator, View } from 'react-native';
import auth from '@react-native-firebase/auth';

import { colors } from '@/theme';
import { useAuthStore } from '@/store/authStore';

// Auth screens
import OnboardingScreen from '@/screens/auth/OnboardingScreen';
import LoginScreen from '@/screens/auth/LoginScreen';
import RegisterScreen from '@/screens/auth/RegisterScreen';
import ProfileSetupScreen from '@/screens/auth/ProfileSetupScreen';

// Main screens
import HomeScreen from '@/screens/main/HomeScreen';
import WardrobeScreen from '@/screens/main/WardrobeScreen';
import AddItemScreen from '@/screens/main/AddItemScreen';
import AnalyticsScreen from '@/screens/main/AnalyticsScreen';
import ProfileScreen from '@/screens/main/ProfileScreen';
import VisualizationScreen from '@/screens/main/VisualizationScreen';
import HistoryScreen from '@/screens/main/HistoryScreen';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

const screenOptions = {
  headerStyle: { backgroundColor: colors.surface },
  headerTintColor: colors.text,
  headerTitleStyle: { fontWeight: '600' as const },
};

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        ...screenOptions,
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopColor: colors.border,
          paddingBottom: 8,
          height: 60,
        },
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarIcon: ({ color, size }) => {
          const icons: Record<string, string> = {
            Home: 'home',
            Wardrobe: 'shirt',
            Analytics: 'leaf',
          };
          return <Ionicons name={(icons[route.name] ?? 'ellipse') as any} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} options={{ title: 'Outfit of the Day' }} />
      <Tab.Screen name="Wardrobe" component={WardrobeScreen} />
      <Tab.Screen name="Analytics" component={AnalyticsScreen} />
    </Tab.Navigator>
  );
}

export default function Navigation() {
  const { user, firebaseReady, setFirebaseReady, syncProfile, setUser } = useAuthStore();

  useEffect(() => {
    const unsubscribe = auth().onAuthStateChanged(async (fbUser) => {
      if (fbUser) {
        await syncProfile();
      } else {
        setUser(null);
      }
      setFirebaseReady(true);
    });
    return unsubscribe;
  }, []);

  if (!firebaseReady) {
    return (
      <View style={{ flex: 1, backgroundColor: colors.background, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator color={colors.primary} size="large" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={screenOptions}>
        {!user ? (
          <>
            <Stack.Screen name="Onboarding" component={OnboardingScreen} options={{ headerShown: false }} />
            <Stack.Screen name="Login" component={LoginScreen} options={{ headerShown: false }} />
            <Stack.Screen name="Register" component={RegisterScreen} options={{ title: 'Create Account' }} />
            <Stack.Screen name="ProfileSetup" component={ProfileSetupScreen} options={{ title: 'Your Profile', headerBackVisible: false }} />
          </>
        ) : (
          <>
            <Stack.Screen name="MainTabs" component={MainTabs} options={{ headerShown: false }} />
            <Stack.Screen name="AddItem" component={AddItemScreen} options={{ title: 'Add Item' }} />
            <Stack.Screen name="Profile" component={ProfileScreen} options={{ title: 'My Profile' }} />
            <Stack.Screen name="Visualization" component={VisualizationScreen} options={{ title: 'Outfit Preview' }} />
            <Stack.Screen name="History" component={HistoryScreen} options={{ title: 'Outfit History' }} />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
