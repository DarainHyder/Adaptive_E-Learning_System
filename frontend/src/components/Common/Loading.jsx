import React from 'react'
import { motion } from 'framer-motion'
import { Loader2 } from 'lucide-react'

const Loading = ({ message = 'Loading...', fullScreen = false }) => {
  const container = fullScreen 
    ? 'fixed inset-0 flex items-center justify-center bg-white/80 backdrop-blur-sm z-50'
    : 'flex items-center justify-center py-12'

  return (
    <div className={container}>
      <div className="text-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="inline-block"
        >
          <Loader2 className="w-12 h-12 text-primary-600" />
        </motion.div>
        
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="mt-4 text-slate-600 font-medium"
        >
          {message}
        </motion.p>
      </div>
    </div>
  )
}

export default Loading