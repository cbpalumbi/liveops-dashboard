import { campaignFriendlyNames } from "../pages/SimulationPage";

export default function DataCampaignItem({ dataCampaign }) {
  return (
    <div className="mb-4 p-4 bg-gray-100 rounded-lg shadow-inner hover:bg-gray-200">
      <h3 className="text-lg font-semibold mb-2">{dataCampaign.name || `Campaign #${dataCampaign.id}`}</h3>
      <p>
        <strong>Tutorial:</strong> {dataCampaign.tutorial?.title || `Tutorial #${dataCampaign.tutorial_id}`}
      </p>
      <p>
        <strong>Type:</strong> {campaignFriendlyNames[dataCampaign.campaign_type.toLowerCase()]}
      </p>
    </div>
  );
}
