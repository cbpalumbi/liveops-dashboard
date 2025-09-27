import { useState } from "react";
import CampaignDetails from "./CampaignDetails";

export default function NotYetRunCampaign({ campaign }) {
    const [isRunning, setIsRunning] = useState(false);

    const [runResponse, setRunResponse] = useState(null);
    const [runError, setRunError] = useState(null);
    const [runSuccess, setRunSuccess] = useState(null);

    const [impressions, setImpressions] = useState(100); 

    async function runCampaign() {
        
        setRunSuccess(null);
        setRunError(null);

        const impressionsValue = parseInt(impressions, 10);
        if (isNaN(impressionsValue) || impressionsValue <= 0) {
            setRunError("Please enter a valid number of impressions greater than 0.");
            return;
        }

        setIsRunning(true);

        const body = {
            data_campaign_id: campaign["id"],
            impressions: impressionsValue
        };

        let post_run_simulation_res = null;
        let post_run_simulation_res_json = null;

        try {
            post_run_simulation_res = await fetch("http://localhost:8000/run_simulation", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            });
            
            post_run_simulation_res_json = await post_run_simulation_res.json();

            if (!post_run_simulation_res.ok) {
                const errorMessage = post_run_simulation_res_json?.detail || `HTTP error ${post_run_simulation_res.status}`;
                throw new Error(errorMessage);
            }

            setRunResponse(post_run_simulation_res_json);
            console.log([post_run_simulation_res_json]);
            setRunSuccess("Success! The simulation is running. The page will now reload.");

            setTimeout(() => {
                window.location.reload();
            }, 1500); 

        } catch (err) {
            setRunError("Could not run simulation. " + err.message);
            // Re-enable the button on error
            setIsRunning(false);
        }
    }

    const buttonClasses = `
        inline-flex items-center px-4 py-2 rounded focus:outline-none mb-4 font-semibold
        transition duration-150 ease-in-out shadow-md
        ${isRunning
            // Style for disabled: turns gray and uses cursor-not-allowed
            ? "bg-gray-400 text-gray-700 cursor-not-allowed"
            // Style for active state 
            : "bg-blue-500 hover:bg-blue-600 text-black active:bg-blue-700"
        }
    `;

    return (
        <div className="p-4 bg-white rounded-lg shadow-inner">
            
            {/* Impressions Input Box */}
            <div className="pb-6">
                <label className="block mb-1 font-bold text-gray-800 text-xl" htmlFor="impressions-input">
                    Number of Impressions
                </label>
                <input
                    id="impressions-input"
                    type="number"
                    min="1"
                    step="1"
                    value={impressions}
                    onChange={(e) => setImpressions(e.target.value)}
                    className="w-45 p-2 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500 shadow-sm"
                    placeholder="e.g., 100000"
                    disabled={isRunning}
                />
            </div>
            
            {/* Run Simulation Button */}
            <button
                onClick={runCampaign}
                disabled={isRunning} 
                className={buttonClasses} 
            >
                {isRunning ? (
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-gray-700" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                ) : (
                    // Play Button Icon (Triangular arrow pointing right)
                    <svg
                        className="w-5 h-5 mr-2"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth={2}
                        viewBox="0 0 24 24"
                        xmlns="http://www.w3.org/2000/svg"
                        aria-hidden="true"
                    >
                        {/* Play symbol path (right-pointing triangle outline) */}
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 20L20 12 5 4V20z" />
                    </svg>
                )}
                <label className="cursor-pointer mb-0">{isRunning ? "Running..." : "Run Simulation"}</label>
            </button>
            {runError && <p className="text-red-600 mt-2 text-sm">{runError}</p>}
            {runSuccess && <p className="text-green-600 mt-2 text-sm">{runSuccess}</p>}
            
            <CampaignDetails
                campaign={campaign}
            />
            
        </div>
    )
}
