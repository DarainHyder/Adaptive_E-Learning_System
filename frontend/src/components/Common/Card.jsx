import React from 'react'
import { motion } from 'framer-motion'

const Card = ({ 
  children, 
  className = '', 
  hover = true,
  gradient = false,
  onClick,
  ...props 
}) => {
  const baseClasses = 'glass-effect rounded-2xl p-6'
  const hoverClasses = hover ? 'hover-lift cursor-pointer' : ''
  const gradientClasses = gradient ? 'bg-gradient-to-br from-primary-50 to-accent-50 border-2 border-primary-100' : ''

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`${baseClasses} ${hoverClasses} ${gradientClasses} ${className}`}
      onClick={onClick}
      {...props}
    >
      {children}
    </motion.div>
  )
}

export default Card