import { useState, useEffect } from "react"
import TutorialList from "../components/TutorialList"


export default function Tutorials() {
    const [campaigns, setCampaigns] = useState([])
    const [selectedCampaignIndex, setSelectedCampaignIndex] = useState(0)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        async function fetchCampaigns() {
            try {
                const res = await fetch("http://localhost:8000/campaigns")
                if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`)
                const data = await res.json()
                setCampaigns(data)
                setSelectedCampaignIndex(0)   
            } catch (err) {
                setError(err.message)
            } finally {
                setLoading(false)
            }
        }
        fetchCampaigns();
    }, [])

    if (loading) return <div>Loading campaigns...</div>
    if (error) return <div className="text-red-600">Error: {error}</div>
    if (campaigns.length === 0) return <div>No campaigns available</div>

    return (
        <div>
            <h1 className="text-2xl font-bold mb-4">Tutorials</h1>
            {/* Dropdown */}
            <select
                value={selectedCampaignIndex}
                onChange={(e) => setSelectedCampaignIndex(Number(e.target.value))}
                className="p-2 border border-gray-300 rounded-lg shadow-sm"
            >
                {campaigns.map((campaign, index) => (
                    <option key={index} value={index}>
                        {campaign.name}
                    </option>
                ))}
            </select>

            {/* Tutorial List */}
            <TutorialList tutorials={campaigns[selectedCampaignIndex]?.tutorials} />
        </div>
    )
}