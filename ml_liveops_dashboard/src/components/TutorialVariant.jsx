import { useState } from 'react';

export default function TutorialVariant({ variant }) {
    const [trueCtr, setTrueCtr] = useState(variant.base_ctr);
    const [isSaving, setIsSaving] = useState(false);
    const [feedback, setFeedback] = useState('');

    const handleInputChange = (e) => {
        const value = e.target.value;
        const floatValue = parseFloat(value);
        if (value === '' || (floatValue >= 0 && floatValue <= 1)) {
            setTrueCtr(value);
            setFeedback(''); 
        } else {
            setFeedback('Value must be between 0 and 1.');
        }
    };

    const handleSave = async () => {
        const floatValue = parseFloat(trueCtr);

        if (floatValue < 0 || floatValue > 1 || isNaN(floatValue)) {
            setFeedback('Invalid True Tutorial Completion value.');
            return;
        }

        setIsSaving(true);
        setFeedback('Saving...');

        const body = {
            base_ctr: floatValue,
        };

        try {
            const patch_variant_res = await fetch(`http://localhost:8000/variant/${variant.id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            });
           
            if (!patch_variant_res.ok) {
                const errorJson = await patch_variant_res.json();
                throw new Error(errorJson.detail || `HTTP error ${patch_variant_res.status}`);
            }

            const updated_variant_data = await patch_variant_res.json();
            
            setTrueCtr(updated_variant_data.base_ctr); 
            setFeedback('Saved successfully!');

        } catch (err) {
            console.error('Error updating CTR:', err); 
            setFeedback(`Error saving CTR: ${err.message}.`);
        } finally {
            setIsSaving(false);
            setTimeout(() => setFeedback(''), 3000); 
        }
    };

    return (
        <div className="flex flex-col mb-8 p-4 border border-gray-200 rounded-lg bg-white">
            <h3 className="text-gray-700 font-semibold mb-3">{variant.name}</h3>
            
            {/* Visual Bar (using variant.color) */}
            <div className={`w-full h-10 ${variant.color} rounded-md shadow-md mb-4`} />
            
            <div className="flex flex-col md:flex-row md:items-center space-y-3 md:space-y-0 md:space-x-6">
                
                {/* Display Current/Input CTR */}
                <div className="flex items-center space-x-2">
                    <label htmlFor={`ctr-input-${variant.id}`} className="text-sm font-medium text-gray-900 w-48">
                        True Tutorial Completion Rate:
                    </label>
                    <input
                        id={`ctr-input-${variant.id}`}
                        type="number"
                        min="0"
                        max="1"
                        step="0.01"
                        value={trueCtr}
                        onChange={handleInputChange}
                        className="w-24 p-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                        aria-describedby={`feedback-${variant.id}`}
                    />
                </div>

                {/* Save Button */}
                <button
                    onClick={handleSave}
                    disabled={isSaving || parseFloat(trueCtr) === variant.base_ctr}
                    className={`px-4 py-2 text-sm font-medium rounded-md shadow-sm transition ease-in-out duration-150 
                        ${isSaving || parseFloat(trueCtr) === variant.base_ctr
                            ? 'bg-gray-400 text-gray-600 cursor-not-allowed'
                            : 'bg-indigo-600 text-gray-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500'
                        }`}
                >
                    {isSaving ? 'Saving...' : 'Save New True Tutorial Completion Rate'}
                </button>
            </div>
            
            {/* Feedback/Error Display */}
            {feedback && (
                <p id={`feedback-${variant.id}`} className={`mt-2 text-xs ${feedback.includes('Error') ? 'text-red-500' : 'text-green-600'}`}>
                    {feedback}
                </p>
            )}
        </div>
    );
}