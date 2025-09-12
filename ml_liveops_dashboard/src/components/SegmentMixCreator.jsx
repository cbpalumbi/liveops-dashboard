import { useState } from 'react';

// This component handles the creation of a new segment mix with entries.
// It receives a list of available segments as a prop and a callback function to handle save.
export default function SegmentMixCreator({ segments, onSave, onCancel, onAddNewSegment }) {
    const [newMixName, setNewMixName] = useState('');
    const [newEntries, setNewEntries] = useState([]);
    const [selectedSegmentId, setSelectedSegmentId] = useState('');
    const [percentage, setPercentage] = useState('');
    const [error, setError] = useState(null);
    const [newSegmentName, setNewSegmentName] = useState('');
    const [showNewSegmentInput, setShowNewSegmentInput] = useState(false);

    const handleAddNewSegment = async (e) => {
        e.preventDefault();
        setError(null);
        if (newSegmentName.trim() === '') {
            setError('Please enter a name for the new segment.');
            return;
        }
         
        const newSegment = {name: newSegmentName.trim() };
        
        // the new id should be the id returned from adding this segment via api
        const newId = await onAddNewSegment(newSegment);

        // Clear the input and hide the field
        setNewSegmentName('');
        setShowNewSegmentInput(false);
        // Automatically select the new segment so the user can add it to the mix
        setSelectedSegmentId(newId.toString()); 
    };

    const handleAddEntry = (e) => {
        e.preventDefault();
        setError(null);
        if (selectedSegmentId === '' || percentage === '') {
            setError("Please select a segment and enter a percentage.");
            return;
        }

        const numericPercentage = parseFloat(percentage);
        if (isNaN(numericPercentage) || numericPercentage <= 0) {
            setError("Percentage must be a positive number.");
            return;
        }

        const existingSegment = newEntries.find(entry => entry.segment.id === parseInt(selectedSegmentId));
        if (existingSegment) {
            setError("This segment has already been added.");
            return;
        }

        const segment = segments.find(s => s.id === parseInt(selectedSegmentId));
        const newEntry = { segment, percentage: numericPercentage };
        setNewEntries([...newEntries, newEntry]);
        setSelectedSegmentId('');
        setPercentage('');
    };

    const handleRemoveEntry = (index) => {
        setNewEntries(newEntries.filter((_, i) => i !== index));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        setError(null);

        if (newMixName.trim() === '') {
            setError("Please enter a name for the new segment mix.");
            return;
        }

        const totalPercentage = newEntries.reduce((sum, entry) => sum + entry.percentage, 0);
        if (Math.round(totalPercentage) !== 100) {
            setError(`Percentages must sum to 100. Current total: ${totalPercentage}`);
            return;
        }

        // Pass the new mix data back to the parent component
        onSave({ name: newMixName, entries: newEntries });
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4 border p-4 rounded-lg shadow-md bg-white">
            <h3 className="text-xl font-semibold">Create New Segment Mix</h3>

            <div>
                <label className="block mb-1 font-semibold" htmlFor="mix-name">
                    Mix Name
                </label>
                <input
                    id="mix-name"
                    type="text"
                    className="w-full p-2 border rounded"
                    value={newMixName}
                    onChange={(e) => setNewMixName(e.target.value)}
                    required
                />
            </div>

            <div className="border p-4 rounded-lg bg-gray-50">
                <h4 className="font-semibold mb-2">Add Segment Entries</h4>
                <div className="flex space-x-2 mb-2">
                    <div className="flex-1">
                        <label className="sr-only" htmlFor="segment-select">Segment</label>
                        <select
                            id="segment-select"
                            className="w-full p-2 border rounded"
                            value={selectedSegmentId}
                            onChange={(e) => setSelectedSegmentId(e.target.value)}
                        >
                            <option value="">Select Segment</option>
                            {segments.map(s => (
                                <option key={s.id} value={s.id}>{s.name}</option>
                            ))}
                        </select>
                    </div>
                    <div className="w-24">
                        <label className="sr-only" htmlFor="percentage-input">Percentage</label>
                        <input
                            id="percentage-input"
                            type="number"
                            className="w-full p-2 border rounded"
                            placeholder="%"
                            value={percentage}
                            onChange={(e) => setPercentage(e.target.value)}
                        />
                    </div>
                    <button
                        type="button"
                        onClick={handleAddEntry}
                        className="px-4 py-2 text-black rounded"
                    >
                        Add
                    </button>
                </div>
                
                {/* New section for creating a segment */}
                {!showNewSegmentInput ? (
                    <div className="mt-2 text-center">
                        <button
                            type="button"
                            onClick={() => setShowNewSegmentInput(true)}
                            className="text-sm text-black hover:underline"
                        >
                            + Add a new segment
                        </button>
                    </div>
                ) : (
                    <div className="flex space-x-2 mt-2">
                        <input
                            type="text"
                            className="w-full p-2 border rounded"
                            placeholder="Enter new segment name"
                            value={newSegmentName}
                            onChange={(e) => setNewSegmentName(e.target.value)}
                        />
                        <button
                            type="button"
                            onClick={handleAddNewSegment}
                            className="px-4 py-2 text-black rounded"
                        >
                            Save
                        </button>
                    </div>
                )}

                <div className="mt-4">
                    <h5 className="font-semibold">Entries:</h5>
                    <ul className="list-disc list-inside space-y-1">
                        {newEntries.map((entry, index) => (
                            <li key={index} className="flex justify-between items-center text-gray-700">
                                <span>{entry.segment.name}: {entry.percentage}%</span>
                                <button 
                                    type="button"
                                    onClick={() => handleRemoveEntry(index)} 
                                    className="text-red-500 hover:text-red-700"
                                >
                                    Remove
                                </button>
                            </li>
                        ))}
                    </ul>
                    {newEntries.length > 0 && (
                        <p className="mt-2 font-bold">Total: {newEntries.reduce((sum, entry) => sum + entry.percentage, 0)}%</p>
                    )}
                </div>
            </div>
            
            {error && <p className="text-red-600 mt-2">{error}</p>}
            
            <div className="flex space-x-2">
                <button
                    type="submit"
                    className="flex-1 px-4 py-2 text-black rounded"
                >
                    Save Mix
                </button>
                <button
                    type="button"
                    onClick={onCancel}
                    className="flex-1 px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400"
                >
                    Cancel
                </button>
            </div>
        </form>
    );
}