import { useState } from 'react'
import {
  ResponsiveContainer, ComposedChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend,
} from 'recharts'

interface Evaluation {
  id: number
  date: string
  weight_kg?: number | null
  height_cm?: number | null
  fat_mass_pct?: number | null
  lean_mass_kg?: number | null
  waist_cm?: number | null
  somatotype_endo?: number | null
  somatotype_meso?: number | null
  somatotype_ecto?: number | null
}

interface Props {
  evaluations: Evaluation[]
}

function calcBmiFromEval(e: Evaluation): number | null {
  if (!e.weight_kg || !e.height_cm || e.height_cm === 0) return null
  return Math.round((e.weight_kg / (e.height_cm / 100) ** 2) * 10) / 10
}

const BODY_METRICS = [
  { key: 'weight_kg',   label: 'Peso (kg)',       color: '#4b7c60', yAxis: 'left'  },
  { key: 'fat_mass_pct',label: '% Grasa',         color: '#c06c52', yAxis: 'right' },
  { key: 'lean_mass_kg',label: 'Masa Magra (kg)', color: '#8da399', yAxis: 'left'  },
  { key: 'bmi',         label: 'IMC',             color: '#6b7280', yAxis: 'left'  },
  { key: 'waist_cm',    label: 'Cintura (cm)',     color: '#d9a441', yAxis: 'left'  },
]

const SOMA_METRICS = [
  { key: 'somatotype_endo', label: 'Endomorfia', color: '#c06c52' },
  { key: 'somatotype_meso', label: 'Mesomorfia', color: '#4b7c60' },
  { key: 'somatotype_ecto', label: 'Ectomorfia', color: '#8da399' },
]

function MetricPill({
  label, color, active, onClick,
}: { label: string; color: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1 rounded-full text-xs font-semibold border transition-colors flex-shrink-0 ${
        active ? 'text-white border-transparent' : 'border-gray-200 text-gray-500 hover:border-gray-300'
      }`}
      style={active ? { backgroundColor: color, borderColor: color } : {}}
    >
      {label}
    </button>
  )
}

export default function IsAkEvolutionChart({ evaluations }: Props) {
  const [activeBody, setActiveBody] = useState<Set<string>>(
    new Set(['weight_kg', 'fat_mass_pct', 'lean_mass_kg'])
  )
  const [activeSoma, setActiveSoma] = useState<Set<string>>(
    new Set(['somatotype_endo', 'somatotype_meso', 'somatotype_ecto'])
  )

  if (evaluations.length < 2) {
    return (
      <div className="text-center text-sm text-gray-400 py-6">
        Se necesitan al menos 2 evaluaciones para mostrar la evolución.
      </div>
    )
  }

  const bodyData = evaluations.map(e => ({
    date: e.date,
    weight_kg: e.weight_kg ?? null,
    fat_mass_pct: e.fat_mass_pct ?? null,
    lean_mass_kg: e.lean_mass_kg ?? null,
    bmi: calcBmiFromEval(e),
    waist_cm: e.waist_cm ?? null,
  }))

  const hasSoma = evaluations.some(e => e.somatotype_endo != null)
  const somaData = hasSoma
    ? evaluations.map(e => ({
        date: e.date,
        somatotype_endo: e.somatotype_endo ?? null,
        somatotype_meso: e.somatotype_meso ?? null,
        somatotype_ecto: e.somatotype_ecto ?? null,
      }))
    : []

  const toggleBody = (key: string) => {
    setActiveBody(prev => {
      const next = new Set(prev)
      if (next.has(key)) { if (next.size > 1) next.delete(key) }
      else next.add(key)
      return next
    })
  }

  const toggleSoma = (key: string) => {
    setActiveSoma(prev => {
      const next = new Set(prev)
      if (next.has(key)) { if (next.size > 1) next.delete(key) }
      else next.add(key)
      return next
    })
  }

  // Somatotype evolution summary
  const firstSoma = somaData[0]
  const lastSoma = somaData[somaData.length - 1]
  const somaArrow = (last: number | null, first: number | null) => {
    if (last == null || first == null) return '—'
    const diff = last - first
    if (Math.abs(diff) < 0.1) return '='
    return diff > 0 ? `↑ +${diff.toFixed(1)}` : `↓ ${diff.toFixed(1)}`
  }

  return (
    <div className="space-y-6">
      {/* Body composition chart */}
      <div>
        <div className="flex flex-wrap gap-2 mb-3">
          {BODY_METRICS.map(m => (
            <MetricPill
              key={m.key}
              label={m.label}
              color={m.color}
              active={activeBody.has(m.key)}
              onClick={() => toggleBody(m.key)}
            />
          ))}
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <ComposedChart data={bodyData} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5EAE7" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis yAxisId="left" tick={{ fontSize: 11 }} width={36} />
            <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} width={32} domain={[0, 50]} />
            <Tooltip />
            <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11 }} />
            {BODY_METRICS.filter(m => activeBody.has(m.key)).map(m => (
              <Line
                key={m.key}
                yAxisId={m.yAxis as 'left' | 'right'}
                type="monotone"
                dataKey={m.key}
                name={m.label}
                stroke={m.color}
                strokeWidth={2}
                dot={{ r: 3 }}
                connectNulls
              />
            ))}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Somatotype chart (only if data exists) */}
      {hasSoma && somaData.length >= 2 && (
        <div>
          <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Somatotipo</h4>
          <div className="flex flex-wrap gap-2 mb-3">
            {SOMA_METRICS.map(m => (
              <MetricPill
                key={m.key}
                label={m.label}
                color={m.color}
                active={activeSoma.has(m.key)}
                onClick={() => toggleSoma(m.key)}
              />
            ))}
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <ComposedChart data={somaData} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5EAE7" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} width={28} domain={[0, 10]} />
              <Tooltip />
              <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11 }} />
              {SOMA_METRICS.filter(m => activeSoma.has(m.key)).map(m => (
                <Line
                  key={m.key}
                  type="monotone"
                  dataKey={m.key}
                  name={m.label}
                  stroke={m.color}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  connectNulls
                />
              ))}
            </ComposedChart>
          </ResponsiveContainer>

          {/* Somatotype summary */}
          {firstSoma && lastSoma && firstSoma.date !== lastSoma.date && (
            <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
              {SOMA_METRICS.map(m => (
                <div key={m.key} className="bg-gray-50 rounded-lg p-2">
                  <div className="font-semibold text-gray-600">{m.label}</div>
                  <div className="text-lg font-bold" style={{ color: m.color }}>
                    {(lastSoma[m.key as keyof typeof lastSoma] as number | null)?.toFixed(1) ?? '—'}
                  </div>
                  <div className="text-gray-400">
                    {somaArrow(
                      lastSoma[m.key as keyof typeof lastSoma] as number | null,
                      firstSoma[m.key as keyof typeof firstSoma] as number | null,
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
