import {
    apiRequest
} from "../../services/api.js";


export async function fetchAnomalyEvents(
    {
        status = "",
        riskLevel = "",
        limit = 100
    } = {}
) {

    const params =
        new URLSearchParams();

    if (status) {
        params.set(
            "status",
            status
        );
    }

    if (riskLevel) {
        params.set(
            "risk_level",
            riskLevel
        );
    }

    params.set(
        "limit",
        String(limit)
    );


    return apiRequest(
        `/access-monitoring/events?${params.toString()}`
    );
}


export async function updateAnomalyStatus(
    anomalyId,
    status
) {

    return apiRequest(
        `/access-monitoring/events/${anomalyId}/status`,
        {
            method: "PATCH",

            body: {
                status
            }
        }
    );
}