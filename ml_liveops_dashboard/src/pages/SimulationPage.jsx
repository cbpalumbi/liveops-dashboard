import { useParams } from "react-router-dom";
import { useEffect, useState, useMemo } from "react";

import RollingCTRChart from "../components/RollingCTRChart";
import ServesPerVariantChart from "../components/ServesPerVariantChart";

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
        async function fetchData() {
            try {
                const [campaignRes, impressionsRes] = await Promise.allSettled([
                    fetch(`http://localhost:8000/data_campaign/${id}`),
                    fetch(`http://localhost:8000/impressions/${id}`)
                ]);

                if (campaignRes.status === "fulfilled") {
                    const res = campaignRes.value;
                    if (!res.ok) throw new Error(`Campaign fetch failed: ${res.status}`);
                    if (!res.headers.get("content-type")?.includes("application/json")) throw new Error("Campaign response is not JSON");
                    setCampaign(await res.json());
                } else {
                    throw new Error("Failed to load campaign");
                }

                if (impressionsRes.status === "fulfilled") {
                    const res = impressionsRes.value;
                    if (!res.ok) throw new Error(`Impressions fetch failed: ${res.status}`);
                    if (!res.headers.get("content-type")?.includes("application/json")) throw new Error("Impressions response is not JSON");
                    setImpressions(await res.json());
                } else {
                    throw new Error("Failed to load impressions");
                }
            } catch (err) {
                console.error(err);
                setError(err.message || "An unexpected error occurred");
            }
        }

        // Initial fetch
        fetchData();

        // Polling every 3 seconds
        const intervalId = setInterval(fetchData, 3000);

        // Cleanup function to clear the interval
        return () => clearInterval(intervalId);
    }, [id]);

    if (!campaign) {
        return (
            <div>Could not fetch simulation from db.</div>
        );
    }
    let campaignName = campaign["campaign_type"].toLowerCase();
    //console.log("hello" + campaignName);
    if (campaignName === "mab") {
        return (
            <div className="p-6">
			<h1 className="text-2xl font-bold mb-5">Simulation {id}</h1>
			{error && <p className="text-red-500">{error}</p>}
            {campaign && <p className="text-3xl font-bold">{campaign["campaign_type"]}</p>}
			{/*impressions.length > 0 && <pre>{JSON.stringify(impressions, null, 2)}</pre>*/}
            <br></br>
            <hr></hr>
            <br></br>
            <ServesPerVariantChart
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
    }
    else if (campaignName === "segmented_mab") {
        return (
            <div>segmented MAB</div>
        );
    } else if (campaignName === "contextual_mab") {
        return (
            <div>contextual MAB</div>
        );
    } else {
        return (
            <div>Unrecognized simulation type.</div>
        );
    }
}
