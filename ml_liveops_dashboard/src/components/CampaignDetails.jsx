
// Helper component to display a single Key/Value pair
const DetailRow = ({ label, value }) => (
    <div className="flex justify-between items-center py-1 px-2 bg-gray-50 rounded">
        <dt className="font-medium text-gray-600">{label}:</dt>
        <dd className="font-semibold text-gray-800">{value}</dd>
    </div>
);

// Helper component to display a single Variant's Base CTR (Unchanged)
const VariantBaseCtrRow = ({ variant }) => (
    <div className="flex justify-between items-center py-1 px-2 bg-gray-100 rounded border-l-4" style={{ borderColor: variant.color || '#ccc' }}>
        <dt className="font-medium text-gray-700">{variant.name || 'Untitled Variant'}</dt>
        <dd className="font-semibold text-gray-900">{(variant.base_ctr).toFixed(2)}</dd>
    </div>
);


// Helper: Displays Segment details AND all associated Segment Variant Modifiers.
const SegmentEntry = ({ entry, index, variants, modifierLookup, showSegmentVariantModifiers }) => {
    const segment = entry.segment;
    const segmentId = segment?.id;

    return (
        <div className="pl-4 border-l-2 border-indigo-200 mt-2">
            <h4 className="text-md font-semibold text-black pb-2">Segment {index + 1}</h4>
            <dl className="space-y-1 text-sm pl-2">
                
                {/* Existing Segment Details */}
                <DetailRow label="Name" value={segment?.name || 'N/A'} />
                <DetailRow label="Percentage" value={`${(entry.percentage).toFixed(0)}%`} />
                
                {/* Segment-Variant Modifiers for this segment */}
                {/* Note: only show these after the campaign has been run */}
                {showSegmentVariantModifiers && variants?.length > 0 && (
                    <div className="pt-2 pb-1 border-t border-gray-200 mt-2">
                        <h5 className="font-semibold text-gray-700 text-xs mb-1">Variant CTR Modifiers (Addition):</h5>
                        <div className="space-y-1 pl-2">
                            {variants.map((variant) => {
                                // Construct the lookup key: "segmentId-variantId"
                                const lookupKey = `${segmentId}-${variant.id}`;
                                
                                // Retrieve the modifier or default to 0.00
                                const modifier = modifierLookup[lookupKey] !== undefined 
                                    ?  modifierLookup[lookupKey]
                                    : 0.00;
                                
                                // Format display: show '+' sign for positive additions
                                const modifierWithSign = modifier >= 0 
                                    ? `+${modifier.toFixed(2)}` 
                                    : `${modifier.toFixed(2)}`;

                                const modifierDisplay = modifierWithSign + ` (Total: ${(variant.base_ctr + modifier).toFixed(2)})`

                                return (
                                    <div key={variant.id} className="text-xs">
                                        <DetailRow 
                                            label={variant.name || `Variant ${variant.id}`} 
                                            value={modifierDisplay} 
                                        />
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}
            </dl>
        </div>
    );
};


export default function CampaignDetails({ campaign }) {
    const isSegmentedMAB = campaign?.campaign_type?.toLowerCase() === 'segmented_mab';
    const variants = campaign?.tutorial?.variants || [];

    // Create a fast lookup map for modifiers: {'segmentId-variantId': modifierValue}
    const modifierLookup = campaign.segment_variant_modifiers?.reduce((acc, mod) => {
        // Ensure keys are strings to match the keys created in SegmentEntry
        acc[`${mod.segment_id}-${mod.variant_id}`] = mod.performance_modifier;
        return acc;
    }, {}) || {};

    return (
        <div>
            <div className="pt-4 mt-4 border-t border-gray-200 max-w-3xl">
                <h3 className="text-xl font-bold text-gray-800 mb-3">Campaign Details</h3>
                <dl className="space-y-2 text-sm">
                    {/* FIELDS ALL CAMPAIGNS SHARE */}
                    <DetailRow label="Tutorial" value={campaign.tutorial.title} />
                    <DetailRow label="Duration (Minutes)" value={campaign.duration} />

                    {/* BASE CTRS PER VARIANT */}
                    {variants.length > 0 && (
                        <div className="pt-4">
                            <h4 className="text-lg font-bold text-gray-700 mb-2 border-b border-gray-300 pb-1">
                                Base Completion Rate Per Variant
                            </h4>
                            <dl className="space-y-2 text-sm">
                                {variants.map((variant) => (
                                    <VariantBaseCtrRow key={variant.id} variant={variant} />
                                ))}
                            </dl>
                        </div>
                    )}

                    {/* SEGMENTED MAB FIELDS */}
                    {isSegmentedMAB && campaign.segment_mix && (
                        <>
                            <div className="pt-4">
                                <h4 className="text-lg font-bold text-gray-700 mb-2 border-b border-gray-300 pb-1">
                                    Segment Mix Details: {campaign.segment_mix.name}
                                </h4>
                                
                                <dl className="space-y-3 text-sm">
                                    {campaign.segment_mix.entries?.map((entry, index) => (
                                        <SegmentEntry 
                                            key={entry.id} 
                                            entry={entry} 
                                            index={index} 
                                            variants={variants}
                                            modifierLookup={modifierLookup}
                                            showSegmentVariantModifiers={campaign["start_time"] != null}
                                        />
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
