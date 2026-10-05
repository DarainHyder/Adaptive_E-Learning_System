import axios from 'axios'
import toast from 'react-hot-toast'

const API_BASE_URL = import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? 'https://sawabedarain-adaptive-elearning-backend.hf.space' : 'http://localhost:7860')
const TOKEN_KEY = 'elearn_token'

export const tokenStore = {
  get: () => {
    try { return localStorage.getItem(TOKEN_KEY) } catch { return null }
  },
  set: (token) => {
    try { token ? localStorage.setItem(TOKEN_KEY, token) : localStorage.removeItem(TOKEN_KEY) } catch { /* private mode */ }
  },
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
  timeout: 120000,
})

// Bearer token works across the Vercel -> Hugging Face origin boundary (third-party cookies are often blocked)
api.interceptors.request.use((config) => {
  const token = tokenStore.get()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const url = error.config?.url || ''
    if (status === 401) {
      tokenStore.set(null)
      if (!url.includes('/api/current-user')) toast.error('Please log in again')
    } else if (!error.config?.silent) {
      const message = error.response?.data?.error ||
        (error.code === 'ECONNABORTED' ? 'The server took too long to respond' : 'Network error, is the backend running?')
      toast.error(message)
    }
    return Promise.reject(error)
  }
)

export const authAPI = {
  login: (credentials) => api.post('/api/login', credentials),
  register: (userData) => api.post('/api/register', userData),
  logout: () => api.post('/api/logout'),
  getCurrentUser: () => api.get('/api/current-user'),
  updateProfile: (data) => api.put('/api/profile', data),
}

export const topicAPI = {
  getAll: () => api.get('/api/topics'),
  getById: (id) => api.get(`/api/topics/${id}`),
}

export const learningAPI = {
  generateLesson: (topicId, fresh = false) => api.post('/api/generate-lesson', { topic_id: topicId, fresh }),
  checkCode: (code) => api.post('/api/check-code', { code }),
  askHint: (data) => api.post('/api/ask-challenge-hint', data),
}

export const quizAPI = {
  generateQuiz: (topicId) => api.post('/api/generate-quiz', { topic_id: topicId }),
  submitAnswer: (data) => api.post('/api/submit-answer', data),
}

export const progressAPI = {
  getKnowledgeState: (topicId) => api.get(`/api/knowledge-state/${topicId}`),
  getKnowledgeStates: () => api.get('/api/knowledge-states'),
  getProgressSummary: () => api.get('/api/progress-summary'),
  getStudyTips: () => api.get('/api/study-tips', { silent: true }),
  getNextTopic: (currentTopicId) =>
    api.get('/api/next-topic', { params: { current_topic_id: currentTopicId }, silent: true }),
  getRecommendations: () => api.get('/api/recommendations', { silent: true }),
  getLearningPath: (topicId) => api.get(`/api/learning-path/${topicId}`),
  getReviewQueue: () => api.get('/api/review-queue', { silent: true }),
}

export const tutorAPI = {
  chat: (message, topicId) => api.post('/api/tutor/chat', { message, topic_id: topicId }),
  history: (topicId) => api.get('/api/tutor/history', { params: { topic_id: topicId }, silent: true }),
  clear: (topicId) => api.delete('/api/tutor/history', { params: { topic_id: topicId } }),
}

export const agentAPI = {
  getStatus: () => api.get('/api/agent-status', { silent: true }),
  getModelInfo: () => api.get('/api/model-info', { silent: true }),
}

export default api
