import { useState, useEffect } from "react";
import DataCampaignList from "../components/DataCampaignList";
import SegmentMixCreator from "../components/SegmentMixCreator";

const MOCK_SEGMENTS = [
  { id: 301, name: "High-Value Shoppers" },
  { id: 302, name: "New Subscribers" },
  { id: 303, name: "Loyalty Members" },
];

const MOCK_SEGMENT_MIXES = [
  { id: 401, name: "Core Audiences" },
  { id: 402, name: "Engaged Users" },
];

export default function Simulations() {
  const [campaigns, setCampaigns] = useState([]);
  const [segments, setSegments] = useState(MOCK_SEGMENTS);
  const [segmentMixes, setSegmentMixes] = useState(MOCK_SEGMENT_MIXES);
  
  const [showForm, setShowForm] = useState(false);
  const [showMixCreator, setShowMixCreator] = useState(false);

  // Form state
  const [formCampaignIndex, setFormCampaignIndex] = useState(0);
  const [formBannerId, setFormBannerId] = useState(null);
  const [formCampaignType, setFormCampaignType] = useState("MAB");
  const [formStartTime, setFormStartTime] = useState("");
  const [formEndTime, setFormEndTime] = useState("");
  const [formSegmentMixId, setFormSegmentMixId] = useState("");
  
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
        if (data.length > 0) {
          setFormCampaignIndex(0);
          if (data[0].banners.length > 0) {
            setFormBannerId(data[0].banners[0].id);
          }
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
  }, [submitSuccess]);

  // Update banner dropdown when campaign changes in form
  useEffect(() => {
    if (campaigns.length > 0) {
      const banners = campaigns[formCampaignIndex]?.banners || [];
      setFormBannerId(banners.length > 0 ? banners[0].id : null);
    }
  }, [formCampaignIndex, campaigns]);

  function handleNewMixCreated() {

  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitError(null);
    setSubmitSuccess(null);

    // Basic validation
    if (formBannerId == null) {
      setSubmitError("Please select a banner");
      return;
    }

    if (formStartTime && formEndTime) {
      const startTime = new Date(formStartTime);
      const endTime = new Date(formEndTime);
      if (endTime <= startTime) {
        setSubmitError("End time must be after the start time.");
        return;
      }
    } 
    else 
    {
      setSubmitError("Please select a start and end time.");
      return;
    }

    const body = {
      campaign_id: campaigns[formCampaignIndex].id,
      banner_id: formBannerId,
      campaign_type: formCampaignType,
      start_time: formStartTime || null,
      end_time: formEndTime || null,
      segment_mix_id: formCampaignType === 'SEGMENTED_MAB' ? formSegmentMixId : null,
    };

    if (formCampaignType === "SEGMENTED_MAB" && isAddingNewMix) {
      console.log("Creating new segment mix with name:", newMixName);
      body.segment_mix_id = 999;
    }


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
        className="inline-flex items-center px-4 py-2 text-black rounded focus:outline-none mb-4"
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
        <label className="mb-1 font-semibold text-black">New Simulation</label>
      </button>

      {/* Form */}
      {showMixCreator ? (
        <SegmentMixCreator
            segments={segments}
            onSave={handleNewMixCreated}
            onCancel={() => setShowMixCreator(false)}
        />  
      ) : (
        showForm && (
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
                <option value="SEGMENTED_MAB">Segmented MAB</option>
                <option value="CONTEXTUAL_MAB">Contextual MAB</option>
                <option value="Random">Random</option>
              </select>
            </div>

            {/* Start and End Time Pickers */}
            <div className="flex space-x-4">
              <div className="flex-1">
                <label className="block mb-1 font-semibold" htmlFor="start-time">
                  Start Time
                </label>
                <input
                  id="start-time"
                  type="date"
                  className="w-full p-2 border rounded"
                  value={formStartTime}
                  onChange={(e) => setFormStartTime(e.target.value)}
                />
              </div>
              <div className="flex-1">
                <label className="block mb-1 font-semibold" htmlFor="end-time">
                  End Time
                </label>
                <input
                  id="end-time"
                  type="date"
                  className="w-full p-2 border rounded"
                  value={formEndTime}
                  onChange={(e) => setFormEndTime(e.target.value)}
                />
              </div>
            </div>
            
            {/* Conditional Fields for SEGMENTED_MAB */}
            {formCampaignType === "SEGMENTED_MAB" && (
              <div className="p-4 border-t border-dashed">
                <h3 className="text-lg font-semibold mb-2">Segmented MAB Options</h3>
                <label className="block mb-1 font-semibold" htmlFor="segment-mix-select">
                  Segment Mix
                </label>
                <select
                  id="segment-mix-select"
                  className="w-full p-2 border rounded"
                  value={formSegmentMixId}
                  onChange={(e) => {
                      const value = e.target.value;
                      if (value === 'new') {
                          setShowMixCreator(true);
                          setShowForm(false);
                      } else {
                          setFormSegmentMixId(value);
                      }
                  }}
                >
                  <option value="" disabled>Select a mix or create new</option>
                  {segmentMixes.map((mix) => (
                      <option key={mix.id} value={mix.id}>{mix.name}</option>
                  ))}
                  <option value="new">-- Add New Mix --</option>
                </select>
              </div>
            )}

            {/* Submit button and messages */}
            <button
              type="submit"
              className="px-4 py-2 bg-green-600 text-black rounded hover:bg-green-700"
            >
              Create Simulation
            </button>

            {submitError && <p className="text-red-600 mt-2">{submitError}</p>}
            {submitSuccess && <p className="text-green-600 mt-2">{submitSuccess}</p>}
          </form>
        )
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
