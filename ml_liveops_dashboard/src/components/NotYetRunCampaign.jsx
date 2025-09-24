import { useState } from "react";

export default function NotYetRunCampaign({ campaign }) {
    const [runResponse, setRunResponse] = useState(null);
    const [runError, setRunError] = useState(null);
    const [runSuccess, setRunSuccess] = useState(null);

    async function runCampaign() {
        setRunSuccess(null);
        setRunError(null);
        const body = {
            data_campaign_id: campaign["id"]
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
                throw new Error(post_run_simulation_res.detail || `HTTP error ${post_run_simulation_res.status}`);
            }
            setRunResponse(post_run_simulation_res_json);
            console.log([post_run_simulation_res_json]);
            setRunSuccess("Success!")
        } catch (err) {
            setRunError("Could not create new segment mix. " + err);
        }
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
            {runError && <p className="text-red-600 mt-2">{runError}</p>}
            {runSuccess && <p className="text-green-600 mt-2">{runSuccess}</p>}
        </div>
    )
}