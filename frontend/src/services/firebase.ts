import { initializeApp, getApp, getApps } from 'firebase/app'
import { getMessaging } from 'firebase/messaging'
import { userService } from './user'
import { getFirebaseApiKey, getFirebaseProjectId, getFirebaseVapidKey } from '@/config/api'

// Check if firebase is configured at runtime
export const isFirebaseSupported = () => {
  const apiKey = getFirebaseApiKey()
  const projectId = getFirebaseProjectId()
  return !!(apiKey && projectId)
}

const getFirebaseConfig = () => ({
  apiKey: getFirebaseApiKey(),
  authDomain: window.APP_CONFIG?.FIREBASE_AUTH_DOMAIN || import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || '',
  projectId: getFirebaseProjectId(),
  messagingSenderId: window.APP_CONFIG?.FIREBASE_MESSAGING_SENDER_ID || import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '',
  appId: window.APP_CONFIG?.FIREBASE_APP_ID || import.meta.env.VITE_FIREBASE_APP_ID || '',
  storageBucket: window.APP_CONFIG?.FIREBASE_STORAGE_BUCKET || import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || '',
  measurementId: window.APP_CONFIG?.FIREBASE_MEASUREMENT_ID || import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || '',
})

export const initializeFirebase = () => {
  if (!isFirebaseSupported()) return null
  
  if (getApps().length === 0) {
    return initializeApp(getFirebaseConfig())
  }
  return getApp()
}

// Safely get messaging instance or return null
export const getSafeMessaging = () => {
  if (!isFirebaseSupported()) return null
  try {
    initializeFirebase()
    return getMessaging()
  } catch (err) {
    console.warn('Failed to initialize Firebase Messaging:', err)
    return null
  }
}

// Export a Proxy for the messaging instance to prevent crashes on import
export const messaging = new Proxy({} as any, {
  get(target, prop) {
    const instance = getSafeMessaging()
    if (!instance) {
      console.warn(`Firebase messaging is not configured. Accessing property '${String(prop)}' returns undefined.`)
      return undefined
    }
    return (instance as any)[prop]
  }
})

export const requestNotificationPermission = async () => {
  if (!isFirebaseSupported()) {
    console.info('Firebase is not configured. Skipping notification permission request.')
    return
  }
  
  try {
    // Check if browser supports notifications
    if (!('Notification' in window)) {
      console.error("Browser doesn't support notifications")
      return
    }

    // Check if permission not already denied
    if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission()
      if (permission === 'granted') {
        const msg = getSafeMessaging()
        if (!msg) return
        
        const { getToken } = await import('firebase/messaging')
        const token = await getToken(msg, {
          vapidKey: getFirebaseVapidKey(),
        })
        // Update FCM token in backend
        await userService.updateFCMToken(token)
      }
    }
  } catch (err) {
    console.error('Failed to get notification permission:', err)
  }
}
