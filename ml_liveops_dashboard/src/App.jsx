import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Tabs from './components/Tabs'
import Tutorials from './pages/Campaigns'
import Simulations from './pages/Simulations'
import SimulationPage from './pages/SimulationPage'

export default function App() {
    return (
      <Router>
        <Layout>
          <Tabs />
          <Routes>
            <Route path="/" element={<Tutorials />} />
            <Route path="/simulations" element={<Simulations />} />
            <Route path="/simulations/:id" element={<SimulationPage />} />
          </Routes>
        </Layout>
      </Router>
    )
}

