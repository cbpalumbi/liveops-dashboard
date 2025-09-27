import TutorialVariant from "./TutorialVariant"

export default function TutorialBase ( { tutorial } ) {
    return (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg shadow-inner">
            <h3 className="text-lg font-semibold mb-4">{tutorial.title}</h3>
            {tutorial.variants.map((variant, index) => (
                <TutorialVariant key={index} variant={variant} />
            ))}
        </div>
    )
}