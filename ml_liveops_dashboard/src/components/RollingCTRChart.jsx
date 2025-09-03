import { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

export default function RollingCTRChart({ rollingCTRData }) {
    const [frame, setFrame] = useState(rollingCTRData.length - 1); // start showing all data
    const [playing, setPlaying] = useState(false);

    useEffect(() => {
        if (!playing) return;
        
        if (frame >= rollingCTRData.length - 1) {
        setPlaying(false);
        return;
        }

        const timer = setTimeout(() => setFrame((f) => f + 1), 200);
        return () => clearTimeout(timer);
    }, [playing, frame, rollingCTRData.length]);

    useEffect(() => {
        setFrame(rollingCTRData.length > 0 ? rollingCTRData.length - 1 : 0);
    }, [rollingCTRData]);

    const onSliderChange = (e) => {
        setFrame(Number(e.target.value));
        if (playing) setPlaying(false); // pause animation when scrubbing manually
    };

    const onPlayClick = () => {
        if (playing) {
        setPlaying(false);
        } else {
        // Restart from beginning only if at the end
        if (frame >= rollingCTRData.length - 1) setFrame(0);
        setPlaying(true);
        }
    };

    return (
        <div>
            <h3 className="text-xl font-semibold mb-3">Rolling CTR</h3>

            <button
                onClick={onPlayClick}
                className="px-4 py-2 bg-blue-600 text-black rounded mb-2"
            >
                {playing ? "Pause" : "Play"}
            </button>

            <input
                type="range"
                min={0}
                max={rollingCTRData.length - 1}
                value={frame}
                onChange={onSliderChange}
                className="w-full mb-4"
            />

            <LineChart
                width={700}
                height={300}
                data={rollingCTRData.slice(0, frame + 1)}
                margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
            >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis domain={[0, 1]} />
                <Tooltip />
                <Line
                type="monotone"
                dataKey="ctr"
                stroke="#82ca9d"
                dot={false}
                strokeWidth={2}
                />
            </LineChart>
        </div>
    );
}
