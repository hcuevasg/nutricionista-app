import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

interface Evaluation {
  id: number
  date: string
  weight_kg?: number | null
  fat_mass_pct?: number | null
  lean_mass_kg?: number | null
}

interface Props {
  evaluations: Evaluation[]
}

export default function IsAkEvolutionChart({ evaluations }: Props) {
  if (evaluations.length < 2) return null

  const data = [...evaluations]
    .sort((a, b) => a.date.localeCompare(b.date))
    .map(ev => ({
      fecha: ev.date,
      'Peso (kg)': ev.weight_kg ?? null,
      '% Grasa': ev.fat_mass_pct ?? null,
      'Masa Magra (kg)': ev.lean_mass_kg ?? null,
    }))

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="font-bold text-primary mb-4 text-sm">Evolución Antropométrica</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5EAE7" />
          <XAxis dataKey="fecha" tick={{ fontSize: 11 }} />
          <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
          <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} />
          <Tooltip
            contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E5EAE7' }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="Peso (kg)"
            stroke="#4b7c60"
            strokeWidth={2}
            dot={{ r: 4 }}
            connectNulls
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="% Grasa"
            stroke="#c06c52"
            strokeWidth={2}
            dot={{ r: 4 }}
            connectNulls
          />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="Masa Magra (kg)"
            stroke="#8da399"
            strokeWidth={2}
            dot={{ r: 4 }}
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
