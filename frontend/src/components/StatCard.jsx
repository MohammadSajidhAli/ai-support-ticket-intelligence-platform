function StatCard({
    title,
    value,
    description,
    icon
}) {

    return (
        <div className="stat-card">

            <div className="stat-header">

                <span>{title}</span>

                <div className="stat-icon">
                    {icon}
                </div>

            </div>

            <h2>{value}</h2>

            <p>{description}</p>

        </div>
    );
}

export default StatCard;