import { useParams } from "react-router-dom";
import { useEffect, useState, useMemo } from "react";

import RollingCTRChart from "../components/RollingCTRChart";
import ServesPerVariantChart from "../components/ServesPerVariantChart";
import SegmentedMABComponent from "../components/SegmentedMABComponent";

export default function SimulationPage() {
	const { id } = useParams();
	const [campaign, setCampaign] = useState(null);
	const [impressions, setImpressions] = useState([]);
	const [error, setError] = useState(null);

    const rollingCTRData = useMemo(() => {
        if (!impressions.length) return [];

        const sorted = [...impressions].sort(
            (a, b) => new Date(a.timestamp) - new Date(b.timestamp)
        );

        let totalServes = 0;
        let totalClicks = 0;

        return sorted.map((imp) => {
            totalServes++;
            if (imp.clicked) totalClicks++;

            return {
            time: new Date(imp.timestamp).toLocaleTimeString(),
            ctr: totalClicks / totalServes,
            };
        });
    }, [impressions]);


	useEffect(() => {
        let intervalId; 

        async function fetchData() {
            try {
                const [campaignRes, impressionsRes] = await Promise.allSettled([
                    fetch(`http://localhost:8000/data_campaign/${id}`),
                    fetch(`http://localhost:8000/impressions/${id}`)
                ]);

                // Process campaign data first to get the end_time
                if (campaignRes.status === "fulfilled" && campaignRes.value.ok) {
                    const campaignData = await campaignRes.value.json();
                    setCampaign(campaignData);

                    // Check end_time for polling logic
                    if (campaignData.end_time && new Date(campaignData.end_time) > new Date()) {
                        // Campaign is active, continue or start polling
                    } else {
                        // Campaign is over, clear the interval
                        if (intervalId) {
                            clearInterval(intervalId);
                        }
                    }
                } else {
                    throw new Error("Failed to load campaign");
                }

                // Process impressions data
                if (impressionsRes.status === "fulfilled" && impressionsRes.value.ok) {
                    const impressionsData = await impressionsRes.value.json();
                    setImpressions(impressionsData);
                } else {
                    throw new Error("Failed to load impressions");
                }

            } catch (err) {
                console.error(err);
                setError(err.message || "An unexpected error occurred");
                if (intervalId) {
                    clearInterval(intervalId);
                }
            }
        }

        // Initial fetch
        fetchData();

        // interval is cleared conditionally inside fetchData
        intervalId = setInterval(fetchData, 3000);

        // Cleanup function
        return () => {
            if (intervalId) {
                clearInterval(intervalId);
            }
        };
    }, [id]); 

    if (!campaign) {
        return (
            <div>Could not fetch simulation from db.</div>
        );
    }

    let campaignType = campaign["campaign_type"].toLowerCase();
    if (campaignType === "mab") {
        return (
            <div className="p-6">
                <SimulationHeader id={id} campaign={campaign} error={error} />
                <br></br>
                <hr></hr>
                <br></br>
                <ServesPerVariantChart
                    impressions={impressions}
                    campaignType={campaignType}
                />
                <hr></hr>
                <br></br>
                <br></br>
                <RollingCTRChart 
                    rollingCTRData={rollingCTRData}
                />
            </div>
        );
    }
    else if (campaignType === "segmented_mab") {
        return (
            <div>
                <SimulationHeader id={id} campaign={campaign} error={error} />
                <SegmentedMABComponent
                    campaign={campaign}
                    impressions={impressions}
                />
                <RollingCTRChart 
                    rollingCTRData={rollingCTRData}
                />
            </div>
        );
    } else if (campaignType === "contextual_mab") {
        return (
            <div>
                <SimulationHeader id={id} campaign={campaign} error={error} />
            </div>
        );
    } else {
        return (
            <div>Unrecognized simulation type.</div>
        );
    }
}

const campaignFriendlyNames = {
  mab: "MAB Campaign",
  segmented_mab: "Segmented MAB Campaign",
  contextual_mab: "Contextual MAB Campaign"
};

function SimulationHeader({ id, campaign, error }) {
    return (
        <div>
            <h1 className="text-2xl font-bold mb-5">Simulation {id}</h1>
            {error && <p className="text-red-500">{error}</p>}
            {campaign && <p className="text-3xl font-bold">{campaignFriendlyNames[campaign["campaign_type"].toLowerCase()]}</p>}
        </div>
    )
}