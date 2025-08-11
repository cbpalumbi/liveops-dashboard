import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Tabs from './components/Tabs'
import Campaigns from './pages/Campaigns'
import Simulations from './pages/Simulations'
import Assets from './pages/Assets'
import SimulationPage from './pages/SimulationPage'

export default function App() {
    return (
      <Router>
        <Layout>
          <Tabs />
          <Routes>
            <Route path="/" element={<Campaigns />} />
            <Route path="/simulations" element={<Simulations />} />
            <Route path="/assets" element={<Assets />} />
            <Route path="/simulations/:id" element={<SimulationPage />} />
          </Routes>
        </Layout>
      </Router>
    )
}

