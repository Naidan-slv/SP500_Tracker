import { Navigate, Route, Routes } from 'react-router-dom'

import { Navbar } from './components/Navbar'
import { DiscoverPage } from './pages/DiscoverPage'
import { StockDetailPage } from './pages/StockDetailPage'

function App() {
  return (
    <div className="app-shell">
      <Navbar />
      <main className="page-container">
        <Routes>
          <Route path="/" element={<DiscoverPage />} />
          <Route path="/stocks/:ticker" element={<StockDetailPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
