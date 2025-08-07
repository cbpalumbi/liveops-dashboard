import BannerBase from "./BannerBase";

export default function BannerList ( { banners } ) {
    return (
        <div className="mt-6">
            {banners.map((banner, index) => (
                <BannerBase key={index} banner={banner} />
        ))}
        </div>
    )
}