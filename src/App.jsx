import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Tabs from './components/Tabs'
import Campaigns from './pages/Campaigns'
import Analytics from './pages/Analytics'
import Assets from './pages/Assets'

export default function App() {
    return (
      <Router>
        <Layout>
          <Tabs />
          <Routes>
            <Route path="/" element={<Campaigns />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/assets" element={<Assets />} />
          </Routes>
        </Layout>
      </Router>
    )
}

