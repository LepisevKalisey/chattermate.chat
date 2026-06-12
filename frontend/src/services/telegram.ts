import api from './api'

// Types
export interface TelegramConfig {
  id: number
  organization_id: string
  agent_id: string
  bot_username: string
  bot_display_name: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface TelegramStatusResponse {
  connected: boolean
  configs: TelegramConfig[]
}

export async function connectTelegramBot(agentId: string, botToken: string): Promise<TelegramConfig> {
  const response = await api.post('/telegram/connect', {
    bot_token: botToken,
    agent_id: agentId
  })
  return response.data
}

export async function getTelegramStatus(): Promise<TelegramStatusResponse> {
  const response = await api.get('/telegram/status')
  return response.data
}

export async function disconnectTelegramBot(configId: number): Promise<void> {
  await api.delete(`/telegram/${configId}`)
}
