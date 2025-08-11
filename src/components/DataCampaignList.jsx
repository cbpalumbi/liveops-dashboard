import { useNavigate } from "react-router-dom";
import DataCampaignItem from "./DataCampaignItem";

export default function DataCampaignList({ dataCampaigns }) {
  const navigate = useNavigate();

  if (!dataCampaigns || dataCampaigns.length === 0)
    return <div className="mt-4 text-gray-500">No data campaigns found</div>;

  return (
    <div className="mt-6">
      {dataCampaigns.map((dc) => (
        <div
          key={dc.id}
          onClick={() => navigate(`/simulations/${dc.id}`)}
          className="cursor-pointer hover:bg-gray-100 transition-colors duration-200 rounded"
        >
          <DataCampaignItem dataCampaign={dc} />
        </div>
      ))}
    </div>
  );
}
