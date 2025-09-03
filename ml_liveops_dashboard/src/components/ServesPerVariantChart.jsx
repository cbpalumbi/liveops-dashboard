import { useState, useEffect } from "react";
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

export default function ServesPerVariantChart({ variantMap, scatterData }) {
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