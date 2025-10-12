import { useState, useCallback } from 'react';

// Helper component for a single editable CTR modifier field
const ModifierInputRow = ({ label, value, onChange }) => (
    <div className="flex justify-between items-center py-1 px-2 bg-white rounded border border-gray-200">
        <label htmlFor={label} className="font-medium text-gray-700 text-sm">{label}:</label>
        <input
            id={label}
            type="number"
            step="0.01"
            min="-1"
            max="1"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="w-24 text-right border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-1"
            placeholder="e.g., 0.25"
        />
    </div>
);

// Main component to edit CTR modifiers
export default function SegVarCTRModifierEditor({ campaign }) {
    const segments = campaign?.segment_mix?.entries?.map(entry => entry.segment) || [];
    const variants = campaign?.tutorial?.variants || [];
    const isSegmentedMAB = campaign?.campaign_type?.toLowerCase() === 'segmented_mab';

   // Helper to find the existing modifier for a segment/variant pair
    const getExistingModifier = (segmentId, variantId) => {
        const modifier = campaign?.segment_variant_modifiers?.find(mod => 
            mod.segment_id === segmentId && mod.variant_id === variantId
        );
        // Load the existing value or default to '0.00' (no addition)
        return modifier ? modifier.performance_modifier.toFixed(2) : '0.00'; 
    };

    // Initialize state by loading existing modifiers from campaign.segment_variant_modifiers
    const initialModifiers = segments.reduce((acc, segment) => {
        acc[segment.id] = variants.reduce((vAcc, variant) => {
            // Load current db value here or default to '0.00'
            vAcc[variant.id] = getExistingModifier(segment.id, variant.id); 
            return vAcc;
        }, {});
        return acc;
    }, {});

    const [modifiers, setModifiers] = useState(initialModifiers);
    const [isSaving, setIsSaving] = useState(false);
    const [saveStatus, setSaveStatus] = useState('');

    if (!isSegmentedMAB || segments.length === 0 || variants.length === 0) {
        return null;
    }

    const handleModifierChange = (segmentId, variantId, newValue) => {
        setModifiers(prevModifiers => ({
            ...prevModifiers,
            [segmentId]: {
                ...prevModifiers[segmentId],
                [variantId]: newValue,
            },
        }));
        setSaveStatus(''); // Clear status when a change is made
    };

const handleSave = useCallback(async () => {
        setIsSaving(true);
        setSaveStatus('Saving...');
        
        const payload = {
            // The endpoint expects a 'modifiers' key containing the list of SegmentVariantPerformanceRequest objects
            modifiers: Object.entries(modifiers).flatMap(([segmentId, variantModifiers]) =>
                Object.entries(variantModifiers).map(([variantId, modifierValue]) => ({
                    segment_id: parseInt(segmentId),
                    variant_id: parseInt(variantId),
                    performance_modifier: parseFloat(modifierValue), 
                }))
            )
        };
        
        console.log('Sending PATCH payload to update modifiers:', payload);
        const endpoint = `http://localhost:8000/campaign/${campaign.id}/modifiers`;     
        try {
            const response = await fetch(endpoint, {
                method: 'PATCH',
                headers: { 
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'No error message provided.' }));
                throw new Error(`Failed to save modifiers: ${response.status} - ${errorData.detail}`);
            }
            
            setSaveStatus('Modifiers saved successfully!');
        } catch (error) {
            console.error('Save failed:', error);
            setSaveStatus(`Error saving modifiers: ${error.message.substring(0, 100)}`);
        } finally {
            setIsSaving(false);
        }
    }, [campaign.id, modifiers]);

    return (
        <div className="pt-4 mt-4 border-b border-gray-200 max-w-3xl">
            <h3 className="text-xl font-bold text-gray-800 mb-3">
                Segment-Specific CTR Modifiers
            </h3>
            <p className="text-sm text-gray-600 mb-4">
                Enter a modifier for each Segment/Variant pair. The final CTR for the segment will be the <strong>Base CTR + Modifier</strong>. 
            </p>

            <div className="space-y-6">
                {segments.map((segment) => (
                    <div key={segment.id} className="p-4 rounded-lg shadow-md bg-gray-50 border-l-4 border-indigo-500">
                        <h4 className="text-lg font-bold text-gray-800 mb-3">
                            Segment: {segment.name || `Segment ${segment.id}`}
                        </h4>
                        
                        <div className="space-y-2 pl-4">
                            {variants.map((variant) => {
                                const fieldLabel = `${variant.name || 'Variant'} Modifier`;
                                return (
                                    <ModifierInputRow
                                        key={variant.id}
                                        label={fieldLabel}
                                        value={modifiers[segment.id][variant.id]}
                                        onChange={(newValue) => 
                                            handleModifierChange(segment.id, variant.id, newValue)
                                        }
                                    />
                                );
                            })}
                        </div>
                    </div>
                ))}
            </div>

            <div className="mt-6 flex items-center justify-between">
                <button
                    onClick={handleSave}
                    disabled={isSaving}
                    className={`px-6 py-2 text-black font-semibold rounded-lg shadow-md transition duration-150 ease-in-out ${
                        isSaving
                            ? 'bg-gray-400 cursor-not-allowed'
                            : 'bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2'
                    }`}
                >
                    {isSaving ? 'Saving...' : 'Save All Modifiers'}
                </button>
                <p className={`text-sm font-medium`}>
                    {saveStatus}
                </p>
            </div>
        </div>
    );
}
