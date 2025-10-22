import { useState, useEffect } from "react";
import DataCampaignList from "../components/DataCampaignList";
import SegmentMixCreator from "../components/SegmentMixCreator";

export default function Simulations() {
  const [tutorials, setTutorials] = useState([]);

  // Data campaigns
  const [dataCampaigns, setDataCampaigns] = useState([]);
  const [dataCampaignsLoading, setDataCampaignsLoading] = useState(true);
  const [dataCampaignsError, setDataCampaignsError] = useState(null);
  const [segmentMixes, setSegmentMixes] = useState([]);
  const [submitSegmentMixSuccess, setSubmitSegmentMixSuccess] = useState(null);
  const [segments, setSegments] = useState([]);
  const [submitSegmentSuccess, setSubmitSegmentSuccess] = useState(null);
  
  const [showForm, setShowForm] = useState(false);
  const [showMixCreator, setShowMixCreator] = useState(false);

  // Form state
  const [formTutorialId, setFormTutorialId] = useState(null);
  const [formCampaignType, setFormCampaignType] = useState("MAB");
  const [formStartTime, setFormStartTime] = useState("");
  const [formEndTime, setFormEndTime] = useState("");
  const [formSegmentMixId, setFormSegmentMixId] = useState("");
  const [selectedSegmentMix, setSelectedSegmentMix] = useState(null);
  const [formDuration, setFormDuration] = useState(1);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [submitError, setSubmitError] = useState(null);
  const [submitSuccess, setSubmitSuccess] = useState(null)

  // Fetch tutorials, existing segments mixes, and existing segments on startup
  useEffect(() => {
    async function fetchStaticCampaigns() {
      try {
        const res = await fetch("http://localhost:8000/tutorials");
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();
        setTutorials(data);
        if (data.length > 0) {
          setFormTutorialId(data[0].id);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchStaticCampaigns();
  }, []);

  useEffect(() => {
    async function fetchSegmentMixes() {
      try {
        const res = await fetch("http://localhost:8000/segment_mixes");
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();
        setSegmentMixes(data);
      } catch (err) {
        setError(err.message);
      }
    }
    fetchSegmentMixes();
  }, [submitSegmentMixSuccess])

  useEffect(() => {
    async function fetchSegments() {
      try {
        const res = await fetch("http://localhost:8000/segments");
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();
        setSegments(data);
      } catch (err) {
        setError(err.message);
      }
    }
    fetchSegments();
  }, [submitSegmentSuccess])

  // Fetch data campaigns on startup or after creating a new one
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

async function handleNewMixCreated (newMix) {
    setSubmitSegmentMixSuccess(null);
    setSubmitError(null); // Clear previous errors

    const mixBody = { name: newMix.name };

    let create_segment_mix_res = null;
    let create_seg_mix_res_json = null;
    let newMixId;

    try {
        create_segment_mix_res = await fetch("http://localhost:8000/segment_mix", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(mixBody),
        });
        
        create_seg_mix_res_json = await create_segment_mix_res.json();
        if (!create_segment_mix_res.ok) {
            throw new Error(create_seg_mix_res_json.detail || `HTTP error ${create_segment_mix_res.status}`);
        }
        newMixId = create_seg_mix_res_json["segment_mix_id"];

        const newSegmentMix = {
            id: newMixId,
            name: newMix.name,
            entries: newMix.entries.map(entry => ({
                segment_mix_id: newMixId,
                segment_id: entry.segment.id,
                percentage: entry.percentage,
                segment: entry.segment 
            }))
        };

        setSegmentMixes(prevMixes => [...prevMixes, newSegmentMix]);
        setFormSegmentMixId(newMixId); // Auto-select the new mix

        const postPromises = newMix.entries.map(entry => {
            const segMixEntryBody = {
                segment_mix_id: newMixId,
                segment_id: entry.segment.id,
                percentage: entry.percentage
            }
            return postSegMixEntry(segMixEntryBody); 
        });

        await Promise.all(postPromises);

        setSubmitSegmentMixSuccess(true);
        setShowMixCreator(false);
        setShowForm(true);

    } catch (err) {
        setSubmitError(`Could not create new segment mix: ${err.message}`);
    }
}

  async function postSegMixEntry(body) {
    try {
        const res = await fetch("http://localhost:8000/segment_mix_entry", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || `HTTP error ${res.status}`);
        }
      } catch (err) {
        setSubmitError("Could not create new segment mix entry.");
      }
  }
  
  async function handleAddNewSegment (newSegment) {
    setSubmitSegmentSuccess(null);
    const body = {
      name: newSegment.name,
      segment_ctr_modifier: newSegment.modifier
    };

    try {
        const res = await fetch("http://localhost:8000/segment", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || `HTTP error ${res.status}`);
        }
        const resJson = await res.json();
        const newSegmentWithId = {
          name: newSegment.name,
          id: resJson.segment_id
        }
        setSegments(prevSegments => [...prevSegments, newSegmentWithId]);
        setSubmitSegmentSuccess(true);
        return resJson.segment_id;
      } catch (err) {
          setSubmitError("Could not create new segment.");
        return null;
      }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitError(null);
    setSubmitSuccess(null);

    // Basic validation
    if (formTutorialId == null) {
      setSubmitError("Please select a tutorial");
      return;
    }

    if (formCampaignType == "SEGMENTED_MAB" && formSegmentMixId == "") {
      setSubmitError("Please select a valid segment mix");
      return;
    } 

    const body = {
      campaign_id: 0,
      tutorial_id: formTutorialId,
      campaign_type: formCampaignType,
      duration: formDuration,
      start_time: formStartTime || null,
      end_time: formEndTime || null,
      segment_mix_id: formCampaignType === 'SEGMENTED_MAB' ? formSegmentMixId : null,
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

  function SegmentedMABInfoBox({ 
        formCampaignType,         
        formSegmentMixId, 
        segmentMixes, 
        setFormSegmentMixId,      
        setShowMixCreator,        
        setShowForm               
    }) {

    if (formCampaignType !== "SEGMENTED_MAB") { return null; }
    const selectedSegmentMix = segmentMixes.find(
      (mix) => mix.id === formSegmentMixId
    );

     // Function to handle the dropdown change
    const handleMixChange = (e) => {
        const value = e.target.value;
        if (value === 'new') {
            setShowMixCreator(true);
            setShowForm(false);
        } else {
            setFormSegmentMixId(value === "" ? "" : Number(value)); 
        }
    };
    
    return (
        <div className="p-4 border-t border-dashed">
            <label className="block mb-1 font-semibold" htmlFor="segment-mix-select">
                Segment Mix
            </label>
            
            {/* --- Conditional rendering based on whether mixes exist --- */}
            {segmentMixes.length === 0 ? (
                <div className="flex items-center justify-between p-3 border rounded bg-gray-50">
                    <span className="text-gray-600">No segment mixes available.</span>
                    <button
                        onClick={() => {
                            setShowMixCreator(true);
                            setShowForm(false);
                        }}
                        className="px-3 text-sm text-black rounded"
                    >
                        Create New Mix
                    </button>
                </div>
            ) : (
                <select
                    id="segment-mix-select"
                    className="w-full p-2 border rounded"
                    value={formSegmentMixId}
                    onChange={handleMixChange}
                >
                    {/* Default/Placeholder Option */}
                    <option value="">Select a mix or create new</option>
                    
                    {/* Dynamic Mix Options */}
                    {segmentMixes.map((mix) => (
                        <option key={mix.id} value={mix.id}>{mix.name}</option> 
                    ))}
                    
                    {/* Create New Option */}
                    <option value="new">-- Add New Mix --</option>
                </select>
            )}

            {/* Display segment mix entries */}
            {selectedSegmentMix && selectedSegmentMix.entries?.length > 0 && (
              <div className="w-full p-2 mt-2 border rounded">
                <h4 className="font-medium mb-1">Segments in Mix:</h4>
                <ul className="list-disc list-inside">
                  {selectedSegmentMix.entries.map((entry, index) => (
                    <li key={index} className="text-sm">
                      <span className="text-gray-700">{entry.segment.name} (modifier: +{entry.segment.segment_ctr_modifier}% )</span>: 
                      <span className="font-bold ml-1">{entry.percentage}%</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
        </div>
    );
  }

  if (loading) return <div>Loading tutorials...</div>;
  if (error) return <div className="text-red-600">Error: {error}</div>;
  if (tutorials.length === 0) return <div>No tutorials available</div>;

  return (
    <div className="p-4 max-w-2xl">
      <h1 className="text-2xl font-bold mb-4">Simulations</h1>

      {/* New Simulation Button */}
      <button
        onClick={() => {
          setError(null);
          setSubmitError(null);
          setSubmitSuccess(null);
          setFormCampaignType("MAB");
          setFormTutorialId(0);
          setFormSegmentMixId(0);

          setShowForm(!showForm)
        }}
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
            onAddNewSegment={handleAddNewSegment}
        />  
      ) : (
        showForm && (
          <form onSubmit={handleSubmit} className="space-y-4 border p-4 rounded shadow-md">

            <div>
              <label className="block mb-1 font-semibold" htmlFor="tutorial-select">
                Tutorial
              </label>
              <select
                id="tutorial-select"
                className="w-full p-2 border rounded"
                value={formTutorialId || ""}
                onChange={(e) => setFormTutorialId(Number(e.target.value))}
                disabled={!tutorials.length}
              >
                {tutorials.map((b) => (
                  <option key={b.id} value={b.id}>
                      {b.title || `Tutorial ${b.id}`}
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
                <option value="MAB">Multi-Armed Bandit (MAB)</option>
                <option value="SEGMENTED_MAB">Segmented MAB</option>
                {/* <option value="CONTEXTUAL_MAB">Contextual MAB with LinUCB</option> */}
              </select>
            </div>
            <div>
              <label className="block mb-1 font-semibold">
                Duration (min)
              </label>
              <input onChange={(e) => setFormDuration(e.target.value)} type="number" step="1" min="1" max="5" defaultValue={1}></input>
            </div>

            <SegmentedMABInfoBox
              formCampaignType={formCampaignType}
              formSegmentMixId={formSegmentMixId}
              segmentMixes={segmentMixes}
              setFormSegmentMixId={setFormSegmentMixId}
              setShowMixCreator={setShowMixCreator}
              setShowForm={setShowForm}
            />

            {/* Conditional Fields for CONTEXTUAL_MAB */}
            {/* Nothing for now */}

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
