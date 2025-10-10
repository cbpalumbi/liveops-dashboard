import ServesPerVariantChart from "./ServesPerVariantChart";

export default function SegmentedMABComponent({ impressions, campaign }) {

    // extract segment_mix_id from the passed-in campaign
    let segmentMixId = campaign["segment_mix_id"];
    if (segmentMixId == null || campaign.segment_mix == null) {
        throw new Error("Campaign passed to SegmentedMABComponent is not of type Segmented MAB.");
    }

    return (
        <div>
            <ServesPerVariantChart
                campaignType={campaign["campaign_type"].toLowerCase()}
                impressions={impressions}
                segments={campaign.segment_mix.entries?.map(entry => entry.segment) ?? []}
            />
        </div>
    )
}