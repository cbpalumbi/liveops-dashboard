import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

export default function ServesPerVariantChart({ impressions, campaignType, segments = []}) {

    // Preprocessing for the line chart
    // Map each variant to a numeric Y value so they plot on separate lines
    const variantMap = {};
    let nextY = 1;
    let isSegmented = campaignType === "segmented_mab";

    //const variantColors = ['#BE2525', '#028A0F', '#0047AB'];
    const redShades = ['#f5a4a4', '#BE2525', '#500101'];
    //const greenShades = ['#77cc80', '#028A0F', '#004900'];
    //const blueShades = ['#8370db', '#0f58be', '#00004C'];
    
    function getColorForImpression(segmentId = null) {
        let color = '#000000';
        if (isSegmented && segmentId !== null) {
            const segmentIndex = segmentId - 1; // segment id is 1-indexed
            color = redShades[segmentIndex];
        } else {
            color = '#BE2525';
        }
        return color;
    }

    function getNameForScatterDataSubset(segmentId) {
        if (segmentId == null) {
            // no segment data
            return "Impressions";
        } else {
            if (segments.length == 0) {
                return "Impressions";
            }
            return segments[segmentId - 1]["name"];
        }
    }

    const scatterData = impressions.reduce((acc, imp) => {
        if (!acc[imp.segment]) {
            acc[imp.segment] = [];
        }
        if (!(imp.variant_id in variantMap)) {
            variantMap[imp.variant_id] = nextY++;
        }

        // map the impression data to the right format and push it into the correct segment array
        acc[imp.segment].push({
            x: new Date(imp.timestamp).getTime(), // milliseconds for Recharts
            y: variantMap[imp.variant_id], 
            variant: imp.variant_id,
            segment: imp.segment
        });

        return acc;
    }, {});
    
    return (
        <div>
            <h3 className="text-gray-800 text-xl font-bold mb-3">Variants Served Over Time</h3>
            <ScatterChart
                width={700}
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
                
                {Object.keys(scatterData).map((segmentId) => {
                    return (
                        <Scatter
                            key={segmentId}
                            name={getNameForScatterDataSubset(segmentId)}
                            fill={getColorForImpression(segmentId)}
                            data={scatterData[segmentId]}
                            shape={(props) => {
                                let color = getColorForImpression(segmentId);
                                return <circle cx={props.cx} cy={props.cy} r={3} fill={color} />;
                            }}
                        />
                    );
                })}
                
            </ScatterChart>     
        </div>
    )
}