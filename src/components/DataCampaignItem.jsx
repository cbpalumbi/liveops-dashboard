export default function DataCampaignItem({ dataCampaign }) {
  return (
    <div className="mb-4 p-4 bg-gray-100 rounded-lg shadow-inner hover:bg-gray-200">
      <h3 className="text-lg font-semibold mb-2">{dataCampaign.name || `Campaign #${dataCampaign.id}`}</h3>
      {/* TODO: Add Campaign name and show banner name properly */}
      <p>
        <strong>Banner:</strong> {dataCampaign.banner?.title || `Banner #${dataCampaign.banner_id}`}
      </p>
      <p>
        <strong>Type:</strong> {dataCampaign.campaign_type}
      </p>
    </div>
  );
}
