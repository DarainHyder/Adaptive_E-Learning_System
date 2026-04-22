import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Bot, ChevronDown, Activity, CheckCircle, Clock } from 'lucide-react'

const AgentStatus = ({ status }) => {
  const [expanded, setExpanded] = useState(false)

  const agentColors = {
    teaching: 'from-blue-500 to-cyan-500',
    assessment: 'from-green-500 to-emerald-500',
    knowledge: 'from-purple-500 to-pink-500',
    tutor: 'from-orange-500 to-red-500',
    recommendation: 'from-indigo-500 to-violet-500'
  }

  const agentNames = {
    teaching: 'Teaching Agent',
    assessment: 'Assessment Agent',
    knowledge: 'Knowledge Tracker',
    tutor: 'Personal Tutor',
    recommendation: 'Path Advisor'
  }

  return (
    <div className="card">
      {/* Header */}
      <div 
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl flex items-center justify-center">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-slate-800">
              AI Multi-Agent System
            </h3>
            <p className="text-sm text-slate-500">
              {Object.keys(status?.sub_agents || {}).length} agents active
            </p>
          </div>
        </div>

        <motion.div
          animate={{ rotate: expanded ? 180 : 0 }}
          transition={{ duration: 0.3 }}
        >
          <ChevronDown className="w-6 h-6 text-slate-400" />
        </motion.div>
      </div>

      {/* Coordinator Stats */}
      <div className="mt-6 grid grid-cols-3 gap-4">
        <div className="text-center p-3 bg-primary-50 rounded-xl">
          <div className="text-2xl font-bold text-primary-600">
            {status?.coordinator?.tasks_coordinated || 0}
          </div>
          <div className="text-xs text-slate-600 font-medium">
            Tasks Coordinated
          </div>
        </div>

        <div className="text-center p-3 bg-accent-50 rounded-xl">
          <div className="text-2xl font-bold text-accent-600">
            {status?.total_memory || 0}
          </div>
          <div className="text-xs text-slate-600 font-medium">
            Total Memory
          </div>
        </div>

        <div className="text-center p-3 bg-green-50 rounded-xl">
          <div className="flex items-center justify-center gap-1">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-semibold text-green-600">Active</span>
          </div>
          <div className="text-xs text-slate-600 font-medium mt-1">
            System Status
          </div>
        </div>
      </div>

      {/* Expanded Agent Details */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="mt-6 space-y-3 border-t border-slate-200 pt-6">
              {Object.entries(status?.sub_agents || {}).map(([key, agent], index) => (
                <motion.div
                  key={key}
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-center justify-between p-4 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 bg-gradient-to-br ${agentColors[key]} rounded-lg flex items-center justify-center`}>
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <div className="font-semibold text-slate-800">
                        {agentNames[key]}
                      </div>
                      <div className="text-xs text-slate-500 flex items-center gap-2">
                        {agent.state === 'completed' && (
                          <span className="flex items-center gap-1 text-green-600">
                            <CheckCircle className="w-3 h-3" />
                            Ready
                          </span>
                        )}
                        {agent.state === 'idle' && (
                          <span className="flex items-center gap-1 text-slate-500">
                            <Clock className="w-3 h-3" />
                            Idle
                          </span>
                        )}
                        {agent.state === 'acting' && (
                          <span className="flex items-center gap-1 text-blue-600">
                            <Activity className="w-3 h-3" />
                            Working
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="text-right">
                    <div className="text-sm font-semibold text-slate-700">
                      {agent.memory_size || 0}
                    </div>
                    <div className="text-xs text-slate-500">
                      memories
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default AgentStatus