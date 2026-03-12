import { Suspense, lazy } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import { Navbar } from './components/Navbar'

const DiscoverPage = lazy(() => import('./pages/DiscoverPage').then((module) => ({ default: module.DiscoverPage })))
const StockDetailPage = lazy(() => import('./pages/StockDetailPage').then((module) => ({ default: module.StockDetailPage })))
const WatchlistsPage = lazy(() => import('./pages/WatchlistsPage').then((module) => ({ default: module.WatchlistsPage })))
const PortfolioPage = lazy(() => import('./pages/PortfolioPage').then((module) => ({ default: module.PortfolioPage })))

function RouteFallback() {
  return <div className="empty-state">Loading page...</div>
}

function App() {
  return (
    <div className="app-shell">
      <div className="app-background-orb orb-one" />
      <div className="app-background-orb orb-two" />
      <Navbar />
      <main className="page-container">
        <Suspense fallback={<RouteFallback />}>
          <Routes>
            <Route path="/" element={<DiscoverPage />} />
            <Route path="/stocks/:ticker" element={<StockDetailPage />} />
            <Route path="/watchlists" element={<WatchlistsPage />} />
            <Route path="/portfolio" element={<PortfolioPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  )
}

export default App
