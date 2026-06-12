import { ref, onMounted } from 'vue'
import { aiService, type AIConfig } from '@/services/ai'

export function useAISetup() {
  const isLoading = ref(false)
  const error = ref<string>('')
  const setupConfig = ref<{
    provider: string
    model: string
    apiKey: string
  }>({
    provider: '',
    model: '',
    apiKey: '',
  })
  
  const hasExistingConfig = ref(false)
  const googleModels = ref<{ value: string, label: string }[]>([])
  const isLoadingGoogleModels = ref(false)

  const fetchGoogleModels = async (apiKey?: string) => {
    try {
      isLoadingGoogleModels.value = true
      googleModels.value = await aiService.getGoogleModels(apiKey)
    } catch (err: any) {
      console.error('Failed to fetch Google Gemini models:', err)
      googleModels.value = []
    } finally {
      isLoadingGoogleModels.value = false
    }
  }

  const providers = [
    { value: 'openai', label: 'OpenAI' },
    { value: 'groq', label: 'Groq' },
    { value: 'google', label: 'Google Gemini' }
    // Below providers are temporarily disabled
    // { value: 'anthropic', label: 'Anthropic' },
    // { value: 'deepseek', label: 'DeepSeek' },
    // { value: 'googlevertex', label: 'Google Vertex AI' },
    // { value: 'mistral', label: 'Mistral' },
    // { value: 'huggingface', label: 'HuggingFace' },
    // { value: 'ollama', label: 'Ollama' },
    // { value: 'xai', label: 'xAI' }
  ]

  const loadExistingConfig = async () => {
    try {
      isLoading.value = true
      error.value = ''
      const config = await aiService.getOrganizationConfig()
      setupConfig.value = {
        provider: config.model_type.toLowerCase(),
        model: config.model_name,
        apiKey: config.api_key
      }
      hasExistingConfig.value = true
      if (setupConfig.value.provider === 'google') {
        await fetchGoogleModels()
      }
    } catch (err: unknown) {
      const response = (err as { response?: { status?: number; data?: { detail?: { details?: string; error?: string } } } }).response;
      if (response?.status !== 404 && response?.data?.detail?.error !== 'AI configuration not found') {
        error.value = response?.data?.detail?.details || response?.data?.detail?.error || 'Failed to load configuration'
      }
      hasExistingConfig.value = false
    } finally {
      isLoading.value = false
    }
  }
  

  const saveAISetup = async (): Promise<boolean> => {
    try {
      error.value = ''
      isLoading.value = true
      
      if (hasExistingConfig.value) {
        return await updateAISetup()
      }
      
      await aiService.setupAI({
        model_type: setupConfig.value.provider.toUpperCase(),
        model_name: setupConfig.value.model,
        api_key: setupConfig.value.apiKey,
      })
      return true
    } catch (err: unknown) {
      const apiError = (err as { response?: { data?: { detail?: { details?: string; error?: string } } } }).response?.data?.detail;
      error.value = apiError?.details || apiError?.error || 'Setup failed. Please try again.'
      return false
    } finally {
      isLoading.value = false
    }
  }
  
  const updateAISetup = async (): Promise<boolean> => {
    try {
      error.value = ''
      isLoading.value = true
      await aiService.updateAI({
        model_type: setupConfig.value.provider.toUpperCase(),
        model_name: setupConfig.value.model,
        api_key: setupConfig.value.apiKey,
      })
      return true
    } catch (err: unknown) {
      const apiError = (err as { response?: { data?: { detail?: { details?: string; error?: string } } } }).response?.data?.detail;
      error.value = apiError?.details || apiError?.error || 'Update failed. Please try again.'
      return false
    } finally {
      isLoading.value = false
    }
  }

  onMounted(() => {
    loadExistingConfig()
  })

  return {
    isLoading,
    error,
    setupConfig,
    providers,
    googleModels,
    isLoadingGoogleModels,
    fetchGoogleModels,
    saveAISetup,
    updateAISetup,
    loadExistingConfig,
    hasExistingConfig
  }
}
