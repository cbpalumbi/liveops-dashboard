export default function TutorialVariant ( { variant } ) {
    return (
        <div className="flex flex-col items-start space-x-4 mb-8">
            <h3 className="text-gray-700 font-medium mb-2">{variant.name}</h3>
            <div className={`w-2xl h-24 ${variant.color} rounded-lg shadow-md`} />
            
        </div>
    )
}