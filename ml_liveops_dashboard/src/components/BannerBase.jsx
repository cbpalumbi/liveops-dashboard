import BannerVariant from "./BannerVariant"

export default function BannerBase ( { banner } ) {
    return (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg shadow-inner">
            <h3 className="text-lg font-semibold mb-4">{banner.title}</h3>
            {banner.variants.map((variant, index) => (
                <BannerVariant key={index} variant={variant} />
            ))}
        </div>
    )
}