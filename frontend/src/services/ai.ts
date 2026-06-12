import  api  from './api'
import type { AIConfigResponse, AISetupResponse } from '@/types/ai'

export interface AIConfig {
  model_type: string;
  model_name: string;
  api_key: string;
}

export const aiService = {
  async getOrganizationConfig(): Promise<AIConfig> {
    const response = await api.get('/ai/config')
    return response.data
  },

  async setupAI(config: AIConfig): Promise<void> {
    await api.post('/ai/setup', config)
  },
  
  async updateAI(config: AIConfig): Promise<void> {
    await api.put('/ai/config', config)
  },

  async getGoogleModels(apiKey?: string): Promise<{ value: string, label: string }[]> {
    const params = apiKey ? { api_key: apiKey } : {}
    const response = await api.get('/ai/google-models', { params })
    return response.data
  }
}
