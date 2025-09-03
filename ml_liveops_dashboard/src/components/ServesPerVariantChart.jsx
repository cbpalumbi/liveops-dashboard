import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from "recharts";

export default function ServesPerVariantChart({ impressions }) {

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
    
    return (
        <div>
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
        </div>
    )
}