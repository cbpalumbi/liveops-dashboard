import { useParams } from "react-router-dom";
import { useEffect, useState, useMemo } from "react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  LineChart,
  Line
} from "recharts";

import RollingCTRChart from "../components/RollingCTRChart";


export default function SimulationPage() {
	const { id } = useParams();
	const [campaign, setCampaign] = useState(null);
	const [impressions, setImpressions] = useState([]);
	const [error, setError] = useState(null);

    // Preprocessing for the line chart
    // Map each variant to a numeric Y value so they plot on separate lines
    const variantMap = {};
    let nextY = 1;

    const scatterData = impressions.map(imp => {
        if (!(imp.variant_id in variantMap)) {
            variantMap[imp.variant_id] = nextY++;
        }
        return {
            x: new Date(imp.timestamp).getTime(), // milliseconds for Recharts
            y: variantMap[imp.variant_id],
            variant: imp.variant_id
        };
    });

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

	return (
		<div className="p-6">
			<h1 className="text-2xl font-bold">Simulation {id}</h1>
			{error && <p className="text-red-500">{error}</p>}
			{/*campaign && <pre>{JSON.stringify(campaign, null, 2)}</pre>*/}
			{/*impressions.length > 0 && <pre>{JSON.stringify(impressions, null, 2)}</pre>*/}
            <br></br>
            <h3 className="text-lg text-center">Variants Served Over Time</h3>
            <ScatterChart
                width={600}
                height={400}
                margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
                >
                <CartesianGrid />
                
                {/* X-axis as time */}
                <XAxis
                    type="number"
                    dataKey="x"
                    domain={['auto', 'auto']}
                    tickFormatter={(unixTime) => new Date(unixTime).toLocaleTimeString()}
                    name="Time"
                />
                
                {/* Y-axis: discrete lines for each variant */}
                <YAxis
                    type="number"
                    dataKey="y"
                    ticks={Object.values(variantMap)}
                    tickFormatter={(y) => {
                    const variantId = Object.keys(variantMap).find(key => variantMap[key] === y);
                    return `Variant ${variantId}`;
                    }}
                    name="Variant"
                    domain={[0, 3]}
                />
                
                <Tooltip
                    labelFormatter={(unixTime) => new Date(unixTime).toLocaleString()}
                    formatter={(value, name, props) => {
                    if (name === 'y') {
                        return `Variant ${props.payload.variant}`;
                    }
                    return value;
                    }}
                />
                
                
                <Legend />
                
                <Scatter
                    name="Serves"
                    data={scatterData}
                    shape={(props) => {
                        const color = props.payload.variant === 1 ? '#8884d8' : '#82ca9d';
                        return <circle cx={props.cx} cy={props.cy} r={3} fill={color} />;
                    }}
                />
            </ScatterChart>
            <hr></hr>
            <br></br>
            <br></br>
            
            <RollingCTRChart 
                rollingCTRData={rollingCTRData}
            />


		</div>
	);
}
