
import { useEffect, useState} from "react";
import ServesPerVariantChart from "./ServesPerVariantChart";

export default function SegmentedMABComponent({ impressions, campaign }) {
    const [segmentMix, setSegmentMix] = useState(null);
    const [segmentMixEntries, setSegmentMixEntries] = useState(null);
    const [segments, setSegments] = useState([]);
    const [error, setError] = useState(null);
    
    // should hit the endpoints relevant to the segmented mab campaign type
        // resolve segment mix, segment mix entries, and segments

    
    // extract segment_mix_id from the passed-in campaign
    let segmentMixId = campaign["segment_mix_id"];
    if (segmentMixId == null) {
        throw new Error("Campaign passed to SegmentedMABComponent is not of type Segmented MAB.");
    }

    async function fetchSegment(segmentId) {
        try {
            const [segmentRes] = await Promise.allSettled([
                fetch(`http://localhost:8000/segment/${segmentId}`),
            ]);

            if (segmentRes.status === "fulfilled") {
                const res = segmentRes.value;
                if (!res.ok) throw new Error(`Segment fetch failed: ${res.status}`);
                if (!res.headers.get("content-type")?.includes("application/json")) throw new Error("Segment response is not JSON");
                const segment = await res.json();
                setSegments(existingSegments => {
                    return [...existingSegments, segment]
                });
            } else {
                throw new Error("Failed to load segment");
            }
        } catch (err) {
            console.error(err);
            setError(err.message || "An unexpected error occurred when fetching segments.");
        }
    };

    
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

                const [segMixEntriesRes] = await Promise.allSettled([
                    fetch(`http://localhost:8000/segment_mix_entries/${segmentMixId}`),
                ]);

                if (segMixEntriesRes.status === "fulfilled") {
                    const res = segMixEntriesRes.value;
                    if (!res.ok) throw new Error(`Segment mix entries fetch failed: ${res.status}`);
                    if (!res.headers.get("content-type")?.includes("application/json")) throw new Error("Segment mix entries response is not JSON");
                    const entries = await res.json();
                    setSegmentMixEntries(entries);

                    entries.forEach( entry => {
                        fetchSegment(entry["segment_id"]);
                    })
                } else {
                    throw new Error("Failed to load segment mix entries");
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
                segments={segments}
            />
        </div>
    )
}