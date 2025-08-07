function addSummaryCard(plan) {
    const summaryDiv = document.createElement('div');
    summaryDiv.className = 'alert alert-info mt-3 mb-3';

    let summaryContent = `
        Information de livraison:

        Commercial: ${plan.commercial_name} (Code: ${plan.commercial_code})

        Date de livraison: ${plan.delivery_date}

        Distance totale: ${plan.total_distance} km
    `;

    // Add revenue information if available
    if (plan.revenue_info) {
        const revenueInfo = plan.revenue_info;
        summaryContent += `
            Analyse du Chiffre d'Affaires:

            CA estimé: ${revenueInfo.estimated_revenue ? revenueInfo.estimated_revenue.toFixed(2) : 'N/A'} TND
        `;

        if (revenueInfo.min_revenue_target) {
            summaryContent += `
                Objectif minimum: ${revenueInfo.min_revenue_target.toFixed(2)} TND
            `;

            if (revenueInfo.meets_target !== undefined) {
                const statusClass = revenueInfo.meets_target ? 'text-success' : 'text-danger';
                const statusText = revenueInfo.meets_target ? 'Objectif atteint' : 'Objectif non atteint';
                summaryContent += `
                    <span class="${statusClass}">${statusText}</span>
                `;

                if (!revenueInfo.meets_target && revenueInfo.revenue_gap) {
                    summaryContent += `
                        Manque: ${revenueInfo.revenue_gap.toFixed(2)} TND
                    `;
                }
            }
        }

        if (revenueInfo.recommendations && revenueInfo.recommendations.length > 0) {
            summaryContent += `
                Recommandations:
                ${revenueInfo.recommendations.map(rec => `<li>${rec}</li>`).join('')}
            `;
        }
    }

    summaryContent += `
        Nombre d'arrêts: ${plan.route.length}
    `;

    summaryDiv.innerHTML = summaryContent;

    // Append the summary card to the desired container
    const container = document.getElementById('summary-container'); // Adjust the container ID as needed
    if (container) {
        container.prepend(summaryDiv);
    }
}
