import { useState, useEffect } from "react";

export default function SimulationPage({ campaign }) {
    const [campaigns, setCampaigns] = useState([]);

    function runCampaign() {

    }

    return (
        <div>
            {/* {campaign["campaign_type"]} */}
            {/* Run Simulation Button */}
            <button
                onClick={() => runCampaign()}
                className="inline-flex items-center px-4 py-2 text-black rounded focus:outline-none mb-4"
            >
                <svg
                className="w-5 h-5 mr-2"
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
                >
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                </svg>
                <label className="mb-1 font-semibold text-black">Run Simulation</label>
            </button>
        </div>
    )
}