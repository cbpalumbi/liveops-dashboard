import { useState, useEffect } from "react";
import DataCampaignList from "../components/DataCampaignList";

export default function Simulations() {
  const [campaigns, setCampaigns] = useState([]);
  const [selectedCampaignIndex, setSelectedCampaignIndex] = useState(0);
  const [showForm, setShowForm] = useState(false);

  // Form state
  const [formCampaignIndex, setFormCampaignIndex] = useState(0);
  const [formBannerId, setFormBannerId] = useState(null);
  const [formCampaignType, setFormCampaignType] = useState("MAB");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [submitError, setSubmitError] = useState(null);
  const [submitSuccess, setSubmitSuccess] = useState(null);

  useEffect(() => {
    async function fetchCampaigns() {
      try {
        const res = await fetch("http://localhost:8000/campaigns");
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();
        setCampaigns(data);
        setSelectedCampaignIndex(0);
        setFormCampaignIndex(0);
        // Set default bannerId for form (if available)
        if (data.length > 0 && data[0].banners.length > 0) {
          setFormBannerId(data[0].banners[0].id);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchCampaigns();
  }, []);

  const [dataCampaigns, setDataCampaigns] = useState([]);
  const [dataCampaignsLoading, setDataCampaignsLoading] = useState(true);
  const [dataCampaignsError, setDataCampaignsError] = useState(null);

  // Fetch data campaigns on load or after creating a new one
  useEffect(() => {
    async function fetchDataCampaigns() {
      try {
        setDataCampaignsLoading(true);
        const res = await fetch("http://localhost:8000/data_campaigns");
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();
        setDataCampaigns(data);
      } catch (err) {
        setDataCampaignsError(err.message);
      } finally {
        setDataCampaignsLoading(false);
      }
    }

    fetchDataCampaigns();
  }, [submitSuccess]); // Reload list after successful creation

  // Update banner dropdown when campaign changes in form
  useEffect(() => {
    if (campaigns.length > 0) {
      const banners = campaigns[formCampaignIndex]?.banners || [];
      setFormBannerId(banners.length > 0 ? banners[0].id : null);
    }
  }, [formCampaignIndex, campaigns]);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitError(null);
    setSubmitSuccess(null);

    if (formBannerId == null) {
      setSubmitError("Please select a banner");
      return;
    }

    const body = {
      campaign_id: campaigns[formCampaignIndex].id,
      banner_id: formBannerId,
      campaign_type: formCampaignType,
    };

    try {
      const res = await fetch("http://localhost:8000/data_campaign", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || `HTTP error ${res.status}`);
      }
      setSubmitSuccess("New simulation created!");
      setShowForm(false);
    } catch (err) {
      setSubmitError(err.message);
    }
  }

  if (loading) return <div>Loading campaigns...</div>;
  if (error) return <div className="text-red-600">Error: {error}</div>;
  if (campaigns.length === 0) return <div>No campaigns available</div>;

  return (
    <div className="p-4 max-w-md">
      <h1 className="text-2xl font-bold mb-4">Simulations</h1>

      {/* New Simulation Button */}
      <button
        onClick={() => setShowForm(!showForm)}
        className="inline-flex items-center px-4 py-2 bg-blue-600 text-black rounded hover:bg-blue-700 focus:outline-none mb-4"
      >
        <svg
          className="w-5 h-5 mr-2"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
        </svg>
        New Simulation
      </button>

      {/* Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="space-y-4 border p-4 rounded shadow-md">
          <div>
            <label className="block mb-1 font-semibold" htmlFor="campaign-select">
              Campaign
            </label>
            <select
              id="campaign-select"
              className="w-full p-2 border rounded"
              value={formCampaignIndex}
              onChange={(e) => setFormCampaignIndex(Number(e.target.value))}
            >
              {campaigns.map((c, i) => (
                <option key={c.id} value={i}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block mb-1 font-semibold" htmlFor="banner-select">
              Banner
            </label>
            <select
              id="banner-select"
              className="w-full p-2 border rounded"
              value={formBannerId || ""}
              onChange={(e) => setFormBannerId(Number(e.target.value))}
              disabled={!campaigns[formCampaignIndex]?.banners.length}
            >
              {campaigns[formCampaignIndex]?.banners.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.title || `Banner ${b.id}`}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block mb-1 font-semibold" htmlFor="campaign-type-select">
              Simulation Type
            </label>
            <select
              id="campaign-type-select"
              className="w-full p-2 border rounded"
              value={formCampaignType}
              onChange={(e) => setFormCampaignType(e.target.value)}
            >
              <option value="MAB">MAB</option>
              <option value="Random">Random</option>
              {/* Add other types if you have them */}
            </select>
          </div>

          <button
            type="submit"
            className="px-4 py-2 bg-green-600 text-black rounded hover:bg-green-700"
          >
            Create Simulation
          </button>

          {submitError && <p className="text-red-600 mt-2">{submitError}</p>}
          {submitSuccess && <p className="text-green-600 mt-2">{submitSuccess}</p>}
        </form>
      )}

      {/* Existing data campaigns list */}
      <h2 className="mt-8 mb-4 text-xl font-semibold">Existing Simulations</h2>
      {dataCampaignsLoading && <div>Loading data campaigns...</div>}
      {dataCampaignsError && <div className="text-red-600">Error: {dataCampaignsError}</div>}

      {!dataCampaignsLoading && !dataCampaignsError && (
        <DataCampaignList dataCampaigns={dataCampaigns} />
      )}

    </div>
  );
}
