
import { useEffect, useState} from "react";
import ServesPerVariantChart from "./ServesPerVariantChart";

export default function SegmentedMABComponent({ impressions, campaign }) {
    const [segmentMix, setSegmentMix] = useState(null);
    const [segments, setSegments] = useState([]);
    const [error, setError] = useState(null);

    // extract segment_mix_id from the passed-in campaign
    let segmentMixId = campaign["segment_mix_id"];
    if (segmentMixId == null) {
        throw new Error("Campaign passed to SegmentedMABComponent is not of type Segmented MAB.");
    }
    
    useEffect(() => {
        async function fetchData() {
            try {
                const [segmentMixRes] = await Promise.allSettled([
                    fetch(`http://localhost:8000/segment_mix/${segmentMixId}`),
                ]);

                if (segmentMixRes.status === "fulfilled") {
                    const res = segmentMixRes.value;
                    if (!res.ok) throw new Error(`Segment mix fetch failed: ${res.status}`);
                    if (!res.headers.get("content-type")?.includes("application/json")) throw new Error("Segment mix response is not JSON");
                    setSegmentMix(await res.json());
                } else {
                    throw new Error("Failed to load segment mix");
                }

            } catch (err) {
                console.error(err);
                setError(err.message || "An unexpected error occurred");
            }
        }

        fetchData();

    }, [segmentMixId]);

    return (
        <div>
            <ServesPerVariantChart
                campaignType={campaign["campaign_type"].toLowerCase()}
                impressions={impressions}
                segments={segmentMix.entries.map(entry => entry.segment) ?? []}
            />
        </div>
    )
}