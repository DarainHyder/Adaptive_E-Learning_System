/**
 * Format date to readable string
 */
export const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

/**
 * Format relative time
 */
export const formatRelativeTime = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffTime = Math.abs(now - date)
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays} days ago`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
  return `${Math.floor(diffDays / 30)} months ago`
}

/**
 * Calculate percentage
 */
export const calculatePercentage = (value, total) => {
  if (total === 0) return 0
  return Math.round((value / total) * 100)
}

/**
 * Get difficulty color
 */
export const getDifficultyColor = (difficulty) => {
  const colors = {
    beginner: 'bg-green-100 text-green-700 border-green-200',
    intermediate: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    advanced: 'bg-red-100 text-red-700 border-red-200'
  }
  return colors[difficulty] || colors.beginner
}

/**
 * Get grade from percentage
 */
export const getGrade = (percentage) => {
  if (percentage >= 90) return { letter: 'A+', color: 'green', message: 'Outstanding!' }
  if (percentage >= 80) return { letter: 'A', color: 'green', message: 'Excellent!' }
  if (percentage >= 70) return { letter: 'B', color: 'blue', message: 'Good Job!' }
  if (percentage >= 60) return { letter: 'C', color: 'yellow', message: 'Keep Practicing!' }
  return { letter: 'F', color: 'red', message: 'Try Again!' }
}

/**
 * Truncate text
 */
export const truncateText = (text, maxLength = 100) => {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

/**
 * Debounce function
 */
export const debounce = (func, wait) => {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

/**
 * Validate email
 */
export const validateEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(email)
}

/**
 * Get knowledge level color
 */
export const getKnowledgeLevelColor = (level) => {
  if (level >= 0.8) return 'from-green-500 to-emerald-500'
  if (level >= 0.6) return 'from-blue-500 to-cyan-500'
  if (level >= 0.4) return 'from-yellow-500 to-orange-500'
  return 'from-red-500 to-pink-500'
}