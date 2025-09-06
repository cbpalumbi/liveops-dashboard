import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from "recharts";

export default function ServesPerVariantChart({ impressions, campaignType }) {

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
            variant: imp.variant_id,
            segment: imp.segment
        };
    });

    let isSegmented = campaignType === "segmented_mab";
    
    const variantColors = ['#BE2525', '#028A0F', '#0047AB'];
    const redShades = ['#f5a4a4', '#BE2525', '#500101'];
    const greenShades = ['#77cc80', '#028A0F', '#004900'];
    const blueShades = ['#8370db', '#0f58be', '#00004C'];
    
    return (
        <div>
            <h3 className="text-xl font-semibold mb-3">Variants Served Over Time</h3>
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
                        // base colors for the variants
                        let color;

                        if (isSegmented && props.payload.segment !== null) {
                            // Use shades based on the variant_id and segment_id
                            const segmentIndex = props.payload.segment - 1; // segment id is 1-indexed
                            if (props.payload.variant === 1) {
                                color = redShades[segmentIndex];
                            } else if (props.payload.variant === 2) {
                                color = greenShades[segmentIndex];
                            } else if (props.payload.variant === 3) {
                                color = blueShades[segmentIndex];
                            } else {
                                color = '#000000';
                            }
                        } else {
                            color = variantColors[props.payload.variant - 1];
                        }

                        return <circle cx={props.cx} cy={props.cy} r={3} fill={color} />;
                    }}
                />
            </ScatterChart>     
        </div>
    )
}