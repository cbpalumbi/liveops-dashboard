import DataCampaignItem from "./DataCampaignItem";

export default function DataCampaignList({ dataCampaigns }) {
  if (!dataCampaigns || dataCampaigns.length === 0)
    return <div className="mt-4 text-gray-500">No data campaigns found</div>;

  return (
    <div className="mt-6">
      {dataCampaigns.map((dc) => (
        <DataCampaignItem key={dc.id} dataCampaign={dc} />
      ))}
    </div>
  );
}
