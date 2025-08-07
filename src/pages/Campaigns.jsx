import { useState } from "react"
import campaignsData from "../data/campaigns.json"
import BannerList from "../components/BannerList"


export default function Campaigns() {
    const [selectedCampaign, setSelectedCampaign] = useState(0) 

    return (
        <div>
            <h1 className="text-2xl font-bold mb-4">Campaigns</h1>
            {/* Dropdown */}
            <select
                value={selectedCampaign}
                onChange={(e) => setSelectedCampaign(Number(e.target.value))}
                className="p-2 border border-gray-300 rounded-lg shadow-sm"
            >
                {campaignsData.map((campaign, index) => (
                <option key={index} value={index}>
                    {campaign.name}
                </option>
                ))}
            </select>

            {/* Banner List */}
            <BannerList banners={campaignsData[selectedCampaign].banners} />
        </div>
    )
}