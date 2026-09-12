import "./ActionCard.css";

function ActionCard({
    title,
    description,
    onClick
}) {
    return (
        <button
            className="action-card"
            type="button"
            onClick={onClick}
        >
            <div className="action-card-accent"></div>

            <div className="action-card-content">
                <h3>{title}</h3>

                {description && (
                    <p>{description}</p>
                )}
            </div>

            <span className="action-card-arrow">
                →
            </span>
        </button>
    );
}

export default ActionCard;