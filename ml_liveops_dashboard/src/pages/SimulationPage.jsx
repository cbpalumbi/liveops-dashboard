import { useParams } from "react-router-dom";
import { useEffect, useState, useMemo } from "react";

import RollingCTRChart from "../components/RollingCTRChart";
import ServesPerVariantChart from "../components/ServesPerVariantChart";
import SegmentedMABComponent from "../components/SegmentedMABComponent";
import NotYetRunCampaign from "../components/NotYetRunCampaign";
import CampaignDetails from "../components/CampaignDetails";
import SimulationResultDetails from "../components/SimulationResultDetails";

export default function SimulationPage() {
	const { id } = useParams();
    const [simulationResult, setSimulationResult] = useState(null)
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
                console.log("Fetching data...");            
                const [simulationResultRes, campaignRes, impressionsRes] = await Promise.allSettled([
                    fetch(`http://localhost:8000/simulation_result/${id}`),
                    fetch(`http://localhost:8000/data_campaign/${id}`),
                    fetch(`http://localhost:8000/impressions/${id}`)
                ]);
                let simulationResultData = null;
                if (simulationResultRes.status === "fulfilled" && simulationResultRes.value.ok) {
                    simulationResultData = await simulationResultRes.value.json();
                    setSimulationResult(simulationResultData);
                    if (!simulationResultData || simulationResultData.completed) {
                        if (intervalId) {
                            clearInterval(intervalId);
                        }
                    }
                    console.log("Simulation result is " + simulationResultData);

                } else {
                    throw new Error("Failed to load simulationResult");
                }

                if (campaignRes.status === "fulfilled" && campaignRes.value.ok) {
                    const campaignData = await campaignRes.value.json();
                    setCampaign(campaignData);
                    
                    if (!campaignData.start_time) {
                        console.log("No start time defined. Campaign has not been run yet.");
                        return;
                    }
                    
                    // check if we need to start or continue the polling interval
                    const currentTime = new Date();
                    const startTime = new Date(campaignData.start_time);
                    const endTime = new Date(campaignData.end_time);

                    const simulationOver = simulationResultData && simulationResultData.completed;

                    if (!simulationOver && startTime < currentTime && currentTime < endTime) {
                        // Campaign is active, start or continue polling
                        if (!intervalId) { // Check to prevent setting multiple intervals
                            intervalId = setInterval(fetchData, 3000);
                        }
                    } else {
                        // Campaign is over or not yet started, clear any existing interval
                        if (intervalId) {
                            clearInterval(intervalId);
                        }
                    }
                } else {
                    throw new Error("Failed to load campaign");
                }

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

        fetchData();

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

    if (campaign["start_time"] == null || impressions == null || impressions.length === 0) {
        return (
            <NotYetRunCampaign
                campaign={campaign}
            />
        );
    }

    let campaignType = campaign["campaign_type"].toLowerCase();
    if (campaignType === "mab") {
        return (
            <div className="p-6">
                <SimulationHeader id={id} campaign={campaign} error={error} />
                <br></br>
                <hr></hr>
                <SimulationResultDetails
                    campaign={campaign}
                    simulationResult={simulationResult} 
                />                
                <CampaignDetails
                    campaign={campaign}
                />
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
                <br></br>
                <hr></hr>
                <SimulationResultDetails
                    campaign={campaign}
                    simulationResult={simulationResult} 
                />   
                <CampaignDetails
                    campaign={campaign}
                />
                <br></br>
                <hr></hr>
                <br></br>
                <SegmentedMABComponent
                    campaign={campaign}
                    impressions={impressions}
                />
                <hr></hr>
                <br></br>
                <br></br>
                <RollingCTRChart 
                    rollingCTRData={rollingCTRData}
                />
            </div>
        );
    } else if (campaignType === "contextual_mab") {
        return (
            <div>
                <SimulationHeader id={id} campaign={campaign} error={error} />
                <CampaignDetails
                    campaign={campaign}
                />
            </div>
        );
    } else {
        return (
            <div>Unrecognized simulation type.</div>
        );
    }
}

export const campaignFriendlyNames = {
  mab: "MAB Campaign",
  segmented_mab: "Segmented MAB Campaign",
  contextual_mab: "Contextual MAB Campaign with LinUCB"
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