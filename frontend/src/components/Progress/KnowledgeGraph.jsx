import React from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

const ChartTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="rounded-xl border border-ink-700 bg-ink-850 px-3.5 py-2.5 text-xs shadow-xl">
      <p className="mb-1 text-sm text-fg">{d.fullName}</p>
      <p className="text-fg-muted">Mastery <span className="text-gold-300">{d.mastery}%</span></p>
      <p className="text-fg-muted">Predicted success <span className="text-fg">{d.predicted}%</span></p>
    </div>
  )
}

const KnowledgeGraph = ({ data }) => {
  const chartData = data
    .filter((t) => t.practice_count > 0)
    .map((t) => ({
      name: t.name.length > 14 ? `${t.name.slice(0, 13)}…` : t.name,
      fullName: t.name,
      mastery: Math.round(t.knowledge_level * 100),
      predicted: Math.round((t.predicted_success?.intermediate || 0) * 100),
    }))
    .sort((a, b) => b.mastery - a.mastery)

  if (!chartData.length) return null

  return (
    <div className="card">
      <div className="mb-6 flex items-center justify-between">
        <p className="text-sm font-medium text-fg">Mastery vs. predicted success</p>
        <div className="flex gap-4 text-xs text-fg-subtle">
          <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-sm bg-gold-400" />Mastery (BKT)</span>
          <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-sm bg-ink-500" />Predicted (transformer)</span>
        </div>
      </div>
      <div style={{ maxWidth: Math.max(chartData.length * 110, 360) }}>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={chartData} barGap={3} barCategoryGap="25%" margin={{ left: -20 }}>
          <CartesianGrid stroke="#27272d" vertical={false} />
          <XAxis dataKey="name" tick={{ fill: '#6f6e69', fontSize: 11 }} axisLine={false} tickLine={false} interval={0} />
          <YAxis domain={[0, 100]} tick={{ fill: '#6f6e69', fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
          <Bar dataKey="mastery" fill="#ddb36a" radius={[4, 4, 0, 0]} maxBarSize={28} />
          <Bar dataKey="predicted" fill="#55555f" radius={[4, 4, 0, 0]} maxBarSize={28} />
        </BarChart>
      </ResponsiveContainer>
      </div>
    </div>
  )
}

export default KnowledgeGraph
