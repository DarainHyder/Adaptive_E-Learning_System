import React from 'react'
import { motion } from 'framer-motion'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts'
import { BarChart3 } from 'lucide-react'

const KnowledgeGraph = ({ data }) => {
  // Prepare chart data
  const chartData = data
    .filter(topic => topic.knowledge_level > 0)
    .map(topic => ({
      name: topic.name.length > 15 ? topic.name.substring(0, 15) + '...' : topic.name,
      fullName: topic.name,
      knowledge: Math.round(topic.knowledge_level * 100),
      confidence: Math.round(topic.confidence * 100),
      practices: topic.practice_count
    }))
    .sort((a, b) => b.knowledge - a.knowledge)

  const getBarColor = (value) => {
    if (value >= 80) return '#10b981' // green
    if (value >= 60) return '#0ea5e9' // blue
    if (value >= 40) return '#f59e0b' // orange
    return '#ef4444' // red
  }

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 rounded-xl shadow-xl border-2 border-primary-100">
          <p className="font-bold text-slate-800 mb-2">{payload[0].payload.fullName}</p>
          <div className="space-y-1 text-sm">
            <p className="text-slate-600">
              <span className="font-semibold">Knowledge:</span> {payload[0].value}%
            </p>
            <p className="text-slate-600">
              <span className="font-semibold">Confidence:</span> {payload[0].payload.confidence}%
            </p>
            <p className="text-slate-600">
              <span className="font-semibold">Practice Sessions:</span> {payload[0].payload.practices}
            </p>
          </div>
        </div>
      )
    }
    return null
  }

  if (chartData.length === 0) {
    return (
      <div className="card">
        <h2 className="text-2xl font-bold text-slate-800 mb-6 flex items-center gap-2">
          <BarChart3 className="w-7 h-7 text-primary-600" />
          Knowledge Levels
        </h2>
        <div className="text-center py-12 text-slate-500">
          <BarChart3 className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <p>Start learning to see your progress</p>
        </div>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="card"
    >
      <h2 className="text-2xl font-bold text-slate-800 mb-6 flex items-center gap-2">
        <BarChart3 className="w-7 h-7 text-primary-600" />
        Knowledge Levels by Topic
      </h2>

      <div className="w-full h-96">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey="name"
              angle={-45}
              textAnchor="end"
              height={100}
              tick={{ fill: '#64748b', fontSize: 12 }}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fill: '#64748b', fontSize: 12 }}
              label={{ value: 'Knowledge %', angle: -90, position: 'insideLeft', fill: '#64748b' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="knowledge" radius={[8, 8, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.knowledge)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="mt-6 flex flex-wrap gap-4 justify-center">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-green-500"></div>
          <span className="text-sm text-slate-600">80-100% (Mastered)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-blue-500"></div>
          <span className="text-sm text-slate-600">60-79% (Good)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-orange-500"></div>
          <span className="text-sm text-slate-600">40-59% (Learning)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-red-500"></div>
          <span className="text-sm text-slate-600">0-39% (Beginner)</span>
        </div>
      </div>
    </motion.div>
  )
}

export default KnowledgeGraph