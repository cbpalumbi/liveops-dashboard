// Helper component to display a single Key/Value pair
const DetailRow = ({ label, value }) => (
    <div className="flex justify-between items-center py-1 px-2 bg-gray-50 rounded">
        <dt className="font-medium text-gray-600">{label}:</dt>
        <dd className="font-semibold text-gray-800">{value}</dd>
    </div>
);

// Helper component to display a single Key/Value pair with a different background for emphasis
const HighlightedDetailRow = ({ label, value, colorClass = 'bg-blue-100' }) => (
    <div className="flex justify-between items-center py-1 px-2 rounded" style={{ backgroundColor: colorClass }}>
        <dt className="font-medium text-blue-800">{label}</dt>
        <dd className="font-bold text-blue-900">{value}</dd>
    </div>
);

const formatNumber = (num) => new Intl.NumberFormat().format(num);

const SegmentResult = ({ segmentEntry, resultData, variantNameLookup }) => {
    const segmentName = segmentEntry?.segment?.name || 'Untitled Segment';
    const segmentPercentage = segmentEntry?.percentage || 0;
    const totalImpressions = resultData.impressions;
    const variantCounts = resultData.variant_counts || {};

    return (
        <div className="pl-4 border-l-2 border-indigo-200 mt-3 bg-white p-2 rounded-lg shadow-sm">
            <h5 className="text-md font-bold text-indigo-700 pb-2 border-b border-indigo-100">{segmentName} ({segmentPercentage}%)</h5>

            <dl className="space-y-1 text-sm pt-2">
                <DetailRow label="Total Impressions" value={formatNumber(totalImpressions)} />
                <DetailRow label="MAB Regret" value={parseInt(resultData.mab_regret).toFixed(2)} />
                <DetailRow label="Uniform Random Regret" value={parseInt(resultData.uniform_regret).toFixed(2)} />
            </dl>

            {/* VARIANT DISTRIBUTION WITHIN THIS SEGMENT */}
            {Object.keys(variantCounts).length > 0 && (
                <div className="pt-3">
                    <h6 className="font-semibold text-gray-700 text-xs mb-1">Impressions Per Variant</h6>
                    <div className="space-y-1 pl-2">
                        {Object.entries(variantCounts).map(([variantId, count]) => {
                            const percent = ((count / totalImpressions) * 100).toFixed(1);
                            return (
                                <HighlightedDetailRow
                                    key={variantId}
                                    label={variantNameLookup[variantId] || `Variant ${variantId}`}
                                    value={`${formatNumber(count)} (${percent}%)`}
                                    colorClass='rgba(238, 242, 255, 1)' // Lighter background for nested detail
                                />
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
};

/**
 * Component to display relevant details from a simulation result.
 */
export default function SimulationResultDetails({ campaign, simulationResult }) {
    // Determine campaign type and get variants
    const isSegmentedMAB = campaign?.campaign_type?.toLowerCase() === 'segmented_mab';
    const variants = campaign?.tutorial?.variants || [];

    // A map for variant names for easy lookup when displaying counts/CTRs
    const variantNameLookup = variants.reduce((acc, variant) => {
        acc[variant.id] = variant.name || `Variant ${variant.id}`;
        return acc;
    }, {});

    if (!simulationResult) {
        return (
            <div className="pt-4 mt-4 border-t border-gray-200 max-w-3xl">
                <h3 className="text-xl font-bold text-gray-800 mb-3">Simulation Result</h3>
                <p className="text-lg text-red-500 font-semibold">
                    Simulation is not yet completed or result data is missing.
                </p>
            </div>
        );
    }

    return (
        <div>
            <div className="pt-4 mt-4 border-t border-gray-200 max-w-3xl">
                <h3 className="text-2xl font-bold text-gray-800 mb-3">Results</h3>
                
                <dl className="space-y-2 text-sm">
                    {/* CORE METRICS */}
                    <div className="pb-4">
                        <h4 className="text-lg font-bold text-black mb-2 border-b border-gray-300 pb-1">
                            Core Metrics
                        </h4>
                        <dl className="space-y-1 pl-2">
                            <HighlightedDetailRow 
                                label="Impressions" 
                                value={formatNumber(simulationResult.total_impressions)} 
                                colorClass='rgba(191, 219, 254, 0.4)' // Light blue
                            />
                            <HighlightedDetailRow 
                                label="MAB Algorithm Regret" 
                                value={parseInt(simulationResult.cumulative_regret_mab).toFixed(2)}
                                colorClass='rgba(191, 219, 254, 0.4)' 
                            />
                            <HighlightedDetailRow 
                                label="Uniform Random Regret" 
                                value={parseInt(simulationResult.cumulative_regret_uniform).toFixed(2)}
                                colorClass='rgba(191, 219, 254, 0.4)' // Light blue
                            />
                            <p className="text-xs text-gray-500 pt-1 pl-3">
                                *Lower regret is better. Regret measures performance loss against the optimal strategy.
                            </p>
                        </dl>
                    </div>

                    {/* VARIANT IMPRESSION COUNTS */}
                    {simulationResult.variant_counts && Object.keys(simulationResult.variant_counts).length > 0 && (
                        <div className="pt-2 pb-4 border-t border-gray-200">
                            <h4 className="text-lg font-bold text-black mb-2 border-b border-gray-300 pb-1">
                                Variant Impression Counts
                            </h4>
                            <dl className="space-y-1 pl-2">
                                {Object.entries(simulationResult.variant_counts).map(([variantId, count]) => {
                                    const percent = ((count / simulationResult.total_impressions) * 100).toFixed(1);
                                    return (
                                        <DetailRow 
                                            key={variantId}
                                            label={variantNameLookup[variantId] || `Variant ${variantId}`} 
                                            value={`${formatNumber(count)} (${percent}%)`}
                                        />
                                    );
                                })}
                            </dl>
                        </div>
                    )}
                    
                    {/* PER-SEGMENT REGRET (SEGMENTED MAB ONLY) */}
                    {isSegmentedMAB && simulationResult.per_segment_regret && Object.keys(simulationResult.per_segment_regret).length > 0 && (
                        <div className="pt-2 pb-4 border-t border-gray-200">
                            <h4 className="text-lg font-bold text-gray-700 mb-2 border-b border-gray-300 pb-1">
                                Per-Segment Performance
                            </h4>
                            <dl className="space-y-3 text-sm">
                                {/* Get the segment mix entries for mapping */}
                                {campaign.segment_mix?.entries && Object.entries(simulationResult.per_segment_regret)
                                    // Filter to ensure we only process result keys that have a corresponding segment entry index
                                    .filter(([indexKey, _]) => campaign.segment_mix.entries[parseInt(indexKey) - 1])
                                    .map(([indexKey, resultData]) => {
                                        // The keys are '1', '2', etc., but JavaScript array is 0-indexed, so we subtract 1.
                                        const segmentIndex = parseInt(indexKey) - 1; 
                                        const segmentEntry = campaign.segment_mix.entries[segmentIndex];
                                        
                                        // We can reuse the variantNameLookup 
                                        return (
                                            <SegmentResult 
                                                key={indexKey}
                                                segmentEntry={segmentEntry}
                                                resultData={resultData}
                                                variantNameLookup={variantNameLookup} 
                                            />
                                        );
                                    })}

                                {campaign.segment_mix?.entries?.length === 0 && (
                                    <p className="text-red-500">Warning: Campaign has Segment Mix but no entries defined.</p>
                                )}
                            </dl>
                        </div>
                    )}

                </dl>
            </div>
        </div>
    );
}