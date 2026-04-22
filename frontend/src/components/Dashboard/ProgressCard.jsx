import React from 'react'
import { motion } from 'framer-motion'

const ProgressCard = ({ icon: Icon, label, value, total, suffix = '', color = 'blue', delay = 0 }) => {
  const colorClasses = {
    blue: 'from-blue-500 to-cyan-500',
    purple: 'from-purple-500 to-pink-500',
    green: 'from-green-500 to-emerald-500',
    orange: 'from-orange-500 to-red-500'
  }

  const percentage = total ? Math.round((value / total) * 100) : 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="card group cursor-pointer"
    >
      <div className="flex items-start justify-between mb-4">
        <div className={`w-12 h-12 bg-gradient-to-br ${colorClasses[color]} rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        
        {total && (
          <div className="text-right">
            <div className="text-xs text-slate-500 font-medium">
              {value} / {total}
            </div>
          </div>
        )}
      </div>

      <div className="mb-2">
        <div className="text-3xl font-bold text-slate-800">
          {value}{suffix}
        </div>
        <div className="text-sm text-slate-600 font-medium">
          {label}
        </div>
      </div>

      {total && (
        <div className="mt-4">
          <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${percentage}%` }}
              transition={{ delay: delay + 0.3, duration: 0.8 }}
              className={`h-full bg-gradient-to-r ${colorClasses[color]} rounded-full`}
            />
          </div>
        </div>
      )}
    </motion.div>
  )
}

export default ProgressCard