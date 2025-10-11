import { campaignFriendlyNames } from "../pages/SimulationPage";

// Helper component to display a single Key/Value pair
const DetailRow = ({ label, value }) => (
    <div className="flex justify-between items-center py-1 px-2 bg-gray-50 rounded">
        <dt className="font-medium text-gray-600">{label}:</dt>
        <dd className="font-semibold text-gray-800">{value}</dd>
    </div>
);

// Helper component to display a single Segment Mix Entry
const SegmentEntry = ({ entry, index }) => (
    <div className="pl-4 border-l-2 border-indigo-200 mt-2">
        <h4 className="text-md font-semibold text-black">Segment {index + 1}</h4>
        <dl className="space-y-1 text-sm pl-2">
            <DetailRow label="Name" value={entry.segment?.name || 'N/A'} />
            <DetailRow label="Percentage" value={`${(entry.percentage).toFixed(0)}%`} />
            <DetailRow label="CTR Modifier" value={entry.segment?.segment_ctr_modifier.toFixed(2)} />
        </dl>
    </div>
);


export default function CampaignDetails({ campaign }) {
    const isSegmentedMAB = campaign?.campaign_type?.toLowerCase() === 'segmented_mab';

    return (
        <div>
            <div className="pt-4 mt-4 border-t border-gray-200 max-w-3xl">
                <h3 className="text-xl font-bold text-gray-800 mb-3">Campaign Details</h3>
                <dl className="space-y-2 text-sm">
                    {/* FIELDS ALL CAMPAIGNS SHARE */}
                    <DetailRow label="Static Campaign ID" value={campaign.static_campaign_id} />
                    <DetailRow label="Tutorial ID" value={campaign.tutorial_id} />
                    <DetailRow label="Campaign Type" value={campaignFriendlyNames[campaign.campaign_type?.toLowerCase()]} />
                    <DetailRow label="Duration (Minutes)" value={campaign.duration} />
                    <DetailRow label="Segment Mix ID" value={campaign.segment_mix_id || "N/A"} />

                    {/* SEGMENTED MAB FIELDS */}
                    {isSegmentedMAB && campaign.segment_mix && (
                        <>
                            <div className="pt-4">
                                <h4 className="text-lg font-bold text-gray-700 mb-2 border-b border-gray-300 pb-1">
                                    Segment Mix Details: {campaign.segment_mix.name}
                                </h4>
                                
                                <dl className="space-y-3 text-sm">
                                    {campaign.segment_mix.entries?.map((entry, index) => (
                                        <SegmentEntry key={entry.id} entry={entry} index={index} />
                                    ))}

                                    {campaign.segment_mix.entries?.length === 0 && (
                                        <p className="text-red-500">Warning: Segment Mix has no entries.</p>
                                    )}
                                </dl>
                            </div>
                        </>
                    )}
                </dl>
            </div>
        </div>
    );
}