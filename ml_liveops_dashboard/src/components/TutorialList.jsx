import TutorialBase from "./TutorialBase";

export default function TutorialList ( { tutorials } ) {
    return (
        <div className="mt-6">
            {tutorials.map((tutorial, index) => (
                <TutorialBase key={index} tutorial={tutorial} />
        ))}
        </div>
    )
}