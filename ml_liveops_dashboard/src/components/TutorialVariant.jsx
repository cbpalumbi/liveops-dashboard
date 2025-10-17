import { useState, useMemo } from 'react';

export default function TutorialVariant({ variant }) {
    // Context vector labels
    const contextLabels = [
        "Age",
        "Sessions Per Day",
        "Avg Session Length (minutes)",
        "Lifetime Spend (USD)",
        "Playstyle Vector 1: Casual",
        "Playstyle Vector 2: Competitive",
        "Playstyle Vector 3: Collector"
    ];

    const parseVectorString = (vectorString) => {
        return vectorString
            // Remove the leading and trailing curly braces, and any whitespace
            .trim()
            .slice(1, -1) // Removes the first '{' and the last '}'
            //  Split the remaining string by the comma and optional space
            .split(',')
            // Map each resulting string element to a float
            .map(str => parseFloat(str.trim()));
    };

    // Initialize the context vector. Use variant data or a default if missing/invalid.
    const initialContextVector = useMemo(() => {
        if (variant.base_params_weights_json && typeof variant.base_params_weights_json === 'string') {
            try {
                const parsedVector = parseVectorString(variant.base_params_weights_json);
                
                if (Array.isArray(parsedVector) && parsedVector.length === 7) {
                    // Convert all elements to floats 
                    return parsedVector.map(v => parseFloat(v));
                }
            } catch (error) {
                console.error("Failed to parse variant.base_params_weights_json:", error);
            }
        }
        // Fallback to default if the string is missing, invalid, or parsing failed
        return [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0];
    }, [variant.base_params_weights_json]); 

    const [trueCtr, setTrueCtr] = useState(variant.base_ctr);
    const [contextVector, setContextVector] = useState(initialContextVector);
    const [showContextVectorMenu, setShowContextVectorMenu] = useState(false);
    
    const [isSaving, setIsSaving] = useState(false);
    const [feedback, setFeedback] = useState('');

    const handleCtrChange = (e) => {
        const value = e.target.value;
        const floatValue = parseFloat(value);
        if (value === '' || (floatValue >= 0 && floatValue <= 1)) {
            setTrueCtr(value);
            setFeedback(''); 
        } else {
            setFeedback('CTR value must be between 0 and 1.');
        }
    };

    const handleContextVectorChange = (index, value) => {
        const floatValue = parseFloat(value);
        
        // Allow empty string for temporary editing, or valid float between 0 and 1
        if (value === '' || (floatValue >= 0 && floatValue <= 1)) {
            setContextVector(prev => {
                const newVector = [...prev];
                newVector[index] = value === '' ? '' : floatValue;
                return newVector;
            });
            setFeedback('');
        } else {
            setFeedback('Context weights must be between 0 and 1.0.');
        }
    };

    const toggleContextVectorMenu = () => {
        setShowContextVectorMenu(prev => !prev);
    };

    const handleSave = async () => {
        const ctrValue = parseFloat(trueCtr);

        // Validate CTR
        if (ctrValue < 0 || ctrValue > 1 || isNaN(ctrValue)) {
            setFeedback('Invalid True Tutorial Completion value.');
            return;
        }

        // Validate Context Vector and create the payload array
        const validContextVector = [];
        for (const val of contextVector) {
            const floatVal = parseFloat(val);
            if (floatVal < 0 || floatVal > 1 || isNaN(floatVal)) {
                setFeedback('One or more context weights are invalid (must be 0 to 1).');
                return;
            }
            validContextVector.push(floatVal);
        }
        
        setIsSaving(true);
        setFeedback('Saving...');

        const vectorString = validContextVector.join(', ');
        const formattedVectorString = `{${vectorString}}`;
        const body = {
            base_ctr: ctrValue,
            base_params_weights_json: formattedVectorString, 
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
            if (updated_variant_data.base_params_weights) {
                 setContextVector(updated_variant_data.base_params_weights.map(v => parseFloat(v)));
            }
            
            setFeedback('Saved successfully!');

        } catch (err) {
            console.error('Error updating variant:', err); 
            setFeedback(`Error saving: ${err.message}.`);
        } finally {
            setIsSaving(false);
            setTimeout(() => setFeedback(''), 3000); 
        }
    };

    const isContextVectorChanged = contextVector.some((val, i) => {
        const currentFloat = parseFloat(val);
        if (isNaN(currentFloat) || val === '') return false;
        return currentFloat !== initialContextVector[i];
    });

    const isCtrChanged = parseFloat(trueCtr) !== variant.base_ctr;
    
    const isSaveDisabled = isSaving || (!isCtrChanged && !isContextVectorChanged);

    return (
        <div className="flex flex-col mb-8 p-6 border border-gray-300 rounded-xl shadow-lg bg-gray-50 font-inter">
            <h3 className="text-xl text-gray-800 font-bold mb-4 border-b pb-2">{variant.name}</h3>
            
            {/* Visual Bar (using variant.color) */}
            <div className={`w-full h-8 ${variant.color || 'bg-blue-300'} rounded-lg shadow-inner mb-6`} />
            
            <div className="flex flex-col space-y-4">
                
                {/* CTR Input and Save Button */}
                <div className="flex flex-col md:flex-row md:items-center space-y-3 md:space-y-0 md:space-x-6">
                    
                    {/* Display Current/Input CTR */}
                    <div className="flex items-center space-x-2 w-full md:w-auto">
                        <label htmlFor={`ctr-input-${variant.id}`} className="text-sm font-medium text-gray-700 min-w-[190px]">
                            True Tutorial Completion Rate:
                        </label>
                        <input
                            id={`ctr-input-${variant.id}`}
                            type="number"
                            min="0"
                            max="1"
                            step="0.01"
                            value={trueCtr}
                            onChange={handleCtrChange}
                            className="w-24 p-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-sm transition"
                            aria-describedby={`feedback-${variant.id}`}
                        />
                    </div>

                    {/* Main Save Button */}
                    <button
                        onClick={handleSave}
                        disabled={isSaveDisabled}
                        className={`px-4 py-2 text-sm font-semibold rounded-lg shadow-md transition ease-in-out duration-200 w-full md:w-auto
                            ${isSaveDisabled
                                ? 'bg-gray-300 text-black cursor-not-allowed'
                                : 'bg-indigo-600 text-black hover:bg-indigo-700 focus:outline-none focus:ring-4 focus:ring-offset-2 focus:ring-indigo-500/50'
                            }`}
                    >
                        {isSaving ? 'Saving...' : 'Save'}
                    </button>
                </div>
                
                {/* Toggle Button for Context Vector Menu */}
                <button
                    onClick={toggleContextVectorMenu}
                    className="mt-4 px-4 py-2 text-sm font-medium rounded-lg shadow-sm transition ease-in-out duration-150 bg-gray-200 text-gray-700 hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-400"
                >
                    {showContextVectorMenu ? 'Hide True Feature Weights' : 'Modify True Feature Weights'}
                </button>
                
                {/* Context Vector Input Menu (Conditionally Rendered) */}
                {showContextVectorMenu && (
                    <div className="p-4 mt-4 bg-white border border-gray-200 rounded-lg shadow-inner grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        <p className="col-span-full text-md font-semibold text-gray-700 mb-2">Feature Weight (0.0 - 1.0)</p>
                        {contextLabels.map((label, index) => (
                            <div key={index} className="flex flex-col space-y-1">
                                <label htmlFor={`context-${index}-${variant.id}`} className="text-xs font-medium text-gray-500">
                                    {label}
                                </label>
                                <input
                                    id={`context-${index}-${variant.id}`}
                                    type="number"
                                    min="0"
                                    max="1"
                                    step="0.01"
                                    value={contextVector[index]}
                                    onChange={(e) => handleContextVectorChange(index, e.target.value)}
                                    className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-green-500 focus:border-green-500 text-sm"
                                />
                            </div>
                        ))}
                    </div>
                )}
                
                {/* Feedback/Error Display */}
                {feedback && (
                    <p id={`feedback-${variant.id}`} className={`mt-2 text-sm font-medium ${feedback.includes('Error') ? 'text-red-600' : 'text-green-600'}`}>
                        {feedback}
                    </p>
                )}
            </div>
        </div>
    );
}
