import axios from 'axios'
import toast from 'react-hot-toast'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.error || 'An error occurred'
    toast.error(message)
    return Promise.reject(error)
  }
)

// Auth APIs
export const authAPI = {
  login: (credentials) => api.post('/api/login', credentials),
  register: (userData) => api.post('/api/register', userData),
  logout: () => api.post('/api/logout'),
  getCurrentUser: () => api.get('/api/current-user'),
}

// Topic APIs
export const topicAPI = {
  getAll: () => api.get('/api/topics'),
  getById: (id) => api.get(`/api/topics/${id}`),
}

// Learning APIs
export const learningAPI = {
  generateLesson: (topicId) => api.post('/api/generate-lesson', { topic_id: topicId }),
  checkCode: (code) => api.post('/api/check-code', { code }),
  askHint: (data) => api.post('/api/ask-challenge-hint', data),
}

// Quiz APIs
export const quizAPI = {
  generateQuiz: (topicId) => api.post('/api/generate-quiz', { topic_id: topicId }),
  submitAnswer: (data) => api.post('/api/submit-answer', data),
}

// Progress APIs
export const progressAPI = {
  getKnowledgeState: (topicId) => api.get(`/api/knowledge-state/${topicId}`),
  getProgressSummary: () => api.get('/api/progress-summary'),
  getStudyTips: () => api.get('/api/study-tips'),
  getNextTopic: (currentTopicId) => 
    api.get('/api/next-topic', { params: { current_topic_id: currentTopicId } }),
}

// Agent APIs
export const agentAPI = {
  getStatus: () => api.get('/api/agent-status'),
}

export default api