import { useState, useEffect } from "react"
import TutorialList from "../components/TutorialList"


export default function Tutorials() {
    const [tutorials, setTutorials] = useState([])
    const [selectedTutorialIndex, setSelectedTutorialIndex] = useState(0)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        async function fetchTutorials() {
            try {
                const res = await fetch("http://localhost:8000/tutorials")
                if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`)
                const data = await res.json()
                setTutorials(data)
                setSelectedTutorialIndex(0)   
            } catch (err) {
                setError(err.message)
            } finally {
                setLoading(false)
            }
        }
        fetchTutorials();
    }, [])

    if (loading) return <div>Loading tutorials...</div>
    if (error) return <div className="text-red-600">Error: {error}</div>
    if (tutorials.length === 0) return <div>No tutorials available</div>

    return (
        <div>
            <h1 className="text-2xl font-bold mb-4">Tutorials</h1>
            {/* Dropdown */}
            <select
                value={selectedTutorialIndex}
                onChange={(e) => setSelectedTutorialIndex(Number(e.target.value))}
                className="p-2 border border-gray-300 rounded-lg shadow-sm"
            >
                {tutorials.map((tutorial, index) => (
                    <option key={index} value={index}>
                        {tutorial.name}
                    </option>
                ))}
            </select>

            {/* Tutorial List */}
            <TutorialList tutorials={tutorials} />
        </div>
    )
}