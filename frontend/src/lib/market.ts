export type MarketFilter = 'all' | 'us' | 'asia' | 'middle-east'

export function getMarketLabel(ticker: string): string {
  if (ticker.endsWith('.KS') || ticker.endsWith('.HK')) {
    return 'Asia'
  }
  if (ticker.endsWith('.SR')) {
    return 'Middle East'
  }
  return 'US'
}

export function matchesMarketFilter(ticker: string, filter: MarketFilter): boolean {
  if (filter === 'all') {
    return true
  }

  const market = getMarketLabel(ticker)

  if (filter === 'us') return market === 'US'
  if (filter === 'asia') return market === 'Asia'
  return market === 'Middle East'
}
