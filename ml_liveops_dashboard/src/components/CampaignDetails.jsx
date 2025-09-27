import { campaignFriendlyNames } from "../pages/SimulationPage"

export default function CampaignDetails({ campaign }) {
    return (
        <div>
            <div className="pt-4 mt-4 border-t border-gray-200 max-w-3xl">
                <h3 className="text-xl font-bold text-gray-800 mb-3">Campaign Details</h3>
                <dl className="space-y-2 text-sm">
                    {/* Static Campaign ID */}
                    <div className="flex justify-between items-center py-1 px-2 bg-gray-50 rounded">
                        <dt className="font-medium text-gray-600">Static Campaign ID:</dt>
                        <dd className="font-semibold text-gray-800">{campaign.static_campaign_id}</dd>
                    </div>
                    {/* Banner ID */}
                    <div className="flex justify-between items-center py-1 px-2 bg-gray-50 rounded">
                        <dt className="font-medium text-gray-600">Banner ID:</dt>
                        <dd className="font-semibold text-gray-800">{campaign.banner_id}</dd>
                    </div>
                    {/* Type */}
                    <div className="flex justify-between items-center py-1 px-2 bg-gray-50 rounded">
                        <dt className="font-medium text-gray-600">Campaign Type:</dt>
                        <dd className="font-semibold text-gray-800">{campaignFriendlyNames[campaign.campaign_type.toLowerCase()]}</dd>
                    </div>
                    {/* Duration */}
                    <div className="flex justify-between items-center py-1 px-2 bg-gray-50 rounded">
                        <dt className="font-medium text-gray-600">Duration (Minutes):</dt>
                        <dd className="font-semibold text-gray-800">{campaign.duration}</dd>
                    </div>
                    {/* Segment Mix ID (Optional) */}
                    <div className="flex justify-between items-center py-1 px-2 bg-gray-50 rounded">
                        <dt className="font-medium text-gray-600">Segment Mix ID:</dt>
                        <dd className="font-semibold text-gray-800">{campaign.segment_mix_id || "N/A"}</dd>
                    </div>
                </dl>
            </div>

        </div>
    )
}