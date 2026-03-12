import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

export function StockHistoryChart({
  data,
}: {
  data: Array<{ date: string; close: number }>
}) {
  return (
    <ResponsiveContainer>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(191, 205, 224, 0.12)" />
        <XAxis dataKey="date" tick={{ fill: '#BFCDE0', fontSize: 12 }} />
        <YAxis tick={{ fill: '#BFCDE0', fontSize: 12 }} domain={['auto', 'auto']} />
        <Tooltip
          contentStyle={{
            background: '#3B3355',
            border: '1px solid rgba(191, 205, 224, 0.18)',
            color: '#FEFCFD',
            borderRadius: 12,
          }}
        />
        <Line type="monotone" dataKey="close" stroke="#BFCDE0" dot={false} strokeWidth={3} />
      </LineChart>
    </ResponsiveContainer>
  )
}