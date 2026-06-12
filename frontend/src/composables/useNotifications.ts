import { onMounted, ref } from 'vue'
import { getMessaging, onMessage, type MessagePayload } from 'firebase/messaging'
import { toast } from 'vue-sonner'
import { requestNotificationPermission, isFirebaseSupported } from '@/services/firebase'
import mitt from '@/utils/emitter'

// Match backend NotificationType enum
enum NotificationType {
  KNOWLEDGE_PROCESSED = 'knowledge_processed',
  KNOWLEDGE_FAILED = 'knowledge_failed',
  SYSTEM = 'system',
  CHAT = 'chat'
}

export function useNotifications() {
  const hasPermission = ref(false)

  const handleNewNotification = (payload: MessagePayload) => {
    const notifType = payload.data?.type || 'default'
    
    // Handle different notification types
    switch (notifType) {
      case NotificationType.KNOWLEDGE_PROCESSED:
        toast.success(payload.notification?.title || 'Knowledge Processing Complete', {
          description: payload.notification?.body,
          duration: 5000,
          position: 'top-right'
        })
        // Emit event to refresh knowledge grid
        mitt.emit('knowledge-updated')
        break

      case NotificationType.KNOWLEDGE_FAILED:
        toast.error(payload.notification?.title || 'Knowledge Processing Failed', {
          description: payload.notification?.body,
          duration: 8000,
          position: 'top-right'
        })
        break

      case NotificationType.SYSTEM:
        toast(payload.notification?.title || 'System Notification', {
          description: payload.notification?.body,
          duration: 5000,
          position: 'top-right'
        })
        break

      case NotificationType.CHAT:
        toast(payload.notification?.title || 'New Chat Message', {
          description: payload.notification?.body,
          duration: 5000,
          position: 'top-right'
        })
        break

      default:
        toast(payload.notification?.title || 'New Notification', {
          description: payload.notification?.body,
          duration: 5000,
          position: 'top-right'
        })
    }
  }

  const listenForBgNotification = () => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('message', (event) => {
        if (event.data?.eventType === 'BACKGROUND_NOTIFICATION') {
          handleNewNotification(event.data)
        }
      })
    }
  }

  const setFcmMessagingListener = async () => {
    const messaging = getMessaging()
    onMessage(messaging, (payload) => {
      handleNewNotification(payload)
    })
  }

  const initializeNotifications = async () => {
    if (!isFirebaseSupported()) {
      console.info('Firebase not configured, skipping notification initialization.')
      return
    }

    try {
      await requestNotificationPermission()
      hasPermission.value = Notification.permission === 'granted'

      if (hasPermission.value) {
        listenForBgNotification()
        await setFcmMessagingListener()
      }
    } catch (err) {
      console.error('Error initializing notifications:', err)
      toast.error('Failed to initialize notifications')
    }
  }

  onMounted(() => {
    initializeNotifications()
  })

  return {
    hasPermission,
    initializeNotifications,
  }
}
