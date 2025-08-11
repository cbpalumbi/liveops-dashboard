import { useParams } from "react-router-dom";

export default function SimulationPage() {
  const { id } = useParams();

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">Simulation {id}</h1>
      <p>This is a placeholder for simulation details.</p>
    </div>
  );
}
