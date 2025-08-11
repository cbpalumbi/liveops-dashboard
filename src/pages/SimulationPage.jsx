import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";

export default function SimulationPage() {
	const { id } = useParams();
	const [campaign, setCampaign] = useState(null);
	const [impressions, setImpressions] = useState([]);
	const [error, setError] = useState(null);

	useEffect(() => {
		async function fetchData() {
			try {
				const [campaignRes, impressionsRes] = await Promise.allSettled([
					fetch(`http://localhost:8000/data_campaign/${id}`),
					fetch(`http://localhost:8000/impressions/${id}`)
				]);

				// Check campaign response
				if (campaignRes.status === "fulfilled") {
					const res = campaignRes.value;
					if (!res.ok) {
						throw new Error(`Campaign fetch failed: ${res.status}`);
					}
                    
					if (!res.headers.get("content-type")?.includes("application/json")) {
						throw new Error("Campaign response is not JSON");
					}
					setCampaign(await res.json());
				} else {
					throw new Error("Failed to load campaign");
				}

				// Check impressions response
				if (impressionsRes.status === "fulfilled") {
					const res = impressionsRes.value;
					if (!res.ok) {
						throw new Error(`Impressions fetch failed: ${res.status}`);
					}
					if (!res.headers.get("content-type")?.includes("application/json")) {
						throw new Error("Impressions response is not JSON");
					}
					setImpressions(await res.json());
				} else {
					throw new Error("Failed to load impressions");
				}
			} catch (err) {
				console.error(err);
				setError(err.message || "An unexpected error occurred");
			}
		}
		fetchData();
	}, [id]);

	return (
		<div className="p-6">
			<h1 className="text-2xl font-bold">Simulation {id}</h1>
			{error && <p className="text-red-500">{error}</p>}
			{campaign && <pre>{JSON.stringify(campaign, null, 2)}</pre>}
			{impressions.length > 0 && <pre>{JSON.stringify(impressions, null, 2)}</pre>}
		</div>
	);
}
