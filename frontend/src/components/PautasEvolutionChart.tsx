import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

interface Pauta {
  id: number
  date: string
  kcal_objetivo?: number | null
  prot_pct?: number | null
  lip_pct?: number | null
  cho_pct?: number | null
}

interface Props {
  pautas: Pauta[]
}

export default function PautasEvolutionChart({ pautas }: Props) {
  if (pautas.length < 2) return null

  const data = [...pautas]
    .sort((a, b) => a.date.localeCompare(b.date))
    .map(p => ({
      fecha: p.date,
      'Kcal objetivo': p.kcal_objetivo ?? null,
      'Proteínas %': p.prot_pct ?? null,
      'Lípidos %': p.lip_pct ?? null,
      'CHO %': p.cho_pct ?? null,
    }))

  return (
    <div className="bg-white rounded-xl shadow-sm border border-border p-6 mt-4">
      <h3 className="font-bold text-sage text-sm mb-4">Evolución de Pautas Nutricionales</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5EAE7" />
          <XAxis dataKey="fecha" tick={{ fontSize: 11 }} />
          <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
          <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} domain={[0, 100]} unit="%" />
          <Tooltip
            contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E5EAE7' }}
            formatter={(value: number, name: string) =>
              name === 'Kcal objetivo' ? [`${value} kcal`, name] : [`${value}%`, name]
            }
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="Kcal objetivo"
            stroke="#8da399"
            strokeWidth={2}
            dot={{ r: 4 }}
            connectNulls
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="Proteínas %"
            stroke="#c06c52"
            strokeWidth={2}
            dot={{ r: 4 }}
            connectNulls
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="Lípidos %"
            stroke="#d9a441"
            strokeWidth={2}
            dot={{ r: 4 }}
            connectNulls
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="CHO %"
            stroke="#4b7c60"
            strokeWidth={2}
            dot={{ r: 4 }}
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
