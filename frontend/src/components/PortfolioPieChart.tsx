import { useMemo, useState } from 'react'
import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Sector,
  Tooltip,
} from 'recharts'

const COLORS = [
  '#BFCDE0',
  '#5D5D81',
  '#69D18D',
  '#FF8F9C',
  '#8B7FD4',
  '#4CC9F0',
  '#F4A261',
  '#E76F51',
  '#A8DADC',
  '#457B9D',
  '#B5838D',
  '#FFB703',
]

const EMPTY_COLOR = 'rgba(93, 93, 129, 0.28)'

type HoldingSlice = {
  ticker: string
  company_name: string | null
  quantity: number
  avg_cost: number | null
}

type Props = {
  holdings: HoldingSlice[]
}

function renderActiveShape(props: any) {
  const {
    cx,
    cy,
    innerRadius,
    outerRadius,
    startAngle,
    endAngle,
    fill,
  } = props

  return (
    <g>
      <Sector
        cx={cx}
        cy={cy}
        innerRadius={innerRadius}
        outerRadius={outerRadius + 6}
        startAngle={startAngle}
        endAngle={endAngle}
        fill={fill}
        stroke="rgba(254,252,253,0.2)"
        strokeWidth={2}
      />
    </g>
  )
}

export function PortfolioPieChart({ holdings }: Props) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null)

  const data = useMemo(() => {
    if (!holdings.length) return []

    const totalValue = holdings.reduce((sum, h) => {
      const value = h.quantity * (h.avg_cost ?? 0)
      return sum + (value > 0 ? value : h.quantity)
    }, 0)

    return holdings.map((h) => {
      const value = h.quantity * (h.avg_cost ?? 0)
      const effectiveValue = value > 0 ? value : h.quantity
      return {
        ticker: h.ticker,
        company_name: h.company_name,
        value: effectiveValue,
        pct: totalValue > 0 ? (effectiveValue / totalValue) * 100 : 0,
      }
    })
  }, [holdings])

  if (!holdings.length) {
    return (
      <div className="pie-chart-container">
        <div className="pie-chart-wrapper">
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={[{ name: 'Empty', value: 1 }]}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                dataKey="value"
                stroke="none"
                isAnimationActive={false}
              >
                <Cell fill={EMPTY_COLOR} />
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="pie-center-label">
            <div className="pie-center-value">0</div>
            <div className="pie-center-desc">holdings</div>
          </div>
        </div>
        <div className="pie-legend-empty">Add holdings to see allocation breakdown.</div>
      </div>
    )
  }

  return (
    <div className="pie-chart-container">
      <div className="pie-chart-wrapper">
        <ResponsiveContainer width="100%" height={260}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              dataKey="value"
              nameKey="ticker"
              stroke="rgba(0,5,5,0.6)"
              strokeWidth={2}
              activeIndex={activeIndex ?? undefined}
              activeShape={renderActiveShape}
              onMouseEnter={(_, index) => setActiveIndex(index)}
              onMouseLeave={() => setActiveIndex(null)}
            >
              {data.map((entry, index) => (
                <Cell
                  key={entry.ticker}
                  fill={COLORS[index % COLORS.length]}
                  opacity={activeIndex === null || activeIndex === index ? 1 : 0.35}
                  style={{ transition: 'opacity 0.2s ease' }}
                />
              ))}
            </Pie>
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null
                const item = payload[0].payload
                return (
                  <div className="pie-tooltip">
                    <strong>{item.ticker}</strong>
                    {item.company_name && (
                      <div className="pie-tooltip-sub">{item.company_name}</div>
                    )}
                    <div className="pie-tooltip-pct">{item.pct.toFixed(1)}%</div>
                  </div>
                )
              }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="pie-center-label">
          <div className="pie-center-value">{holdings.length}</div>
          <div className="pie-center-desc">
            {holdings.length === 1 ? 'holding' : 'holdings'}
          </div>
        </div>
      </div>

      <div className="pie-legend">
        {data.map((entry, index) => (
          <div
            key={entry.ticker}
            className={`pie-legend-item ${activeIndex === index ? 'active' : ''}`}
            onMouseEnter={() => setActiveIndex(index)}
            onMouseLeave={() => setActiveIndex(null)}
          >
            <span
              className="pie-legend-dot"
              style={{ background: COLORS[index % COLORS.length] }}
            />
            <span className="pie-legend-ticker">{entry.ticker}</span>
            <span className="pie-legend-pct">{entry.pct.toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}
