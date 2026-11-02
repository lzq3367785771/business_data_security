import {
    apiRequest
} from "../../services/api.js";


export async function fetchAnomalyEvents(
    {
        status = "",
        riskLevel = "",
        minRiskScore = "",
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

    if (
        minRiskScore !== "" &&
        minRiskScore !== null &&
        minRiskScore !== undefined
    ) {
        params.set(
            "min_risk_score",
            String(minRiskScore)
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

export async function fetchAnomalySummary() {

    return apiRequest(
        "/access-monitoring/events/summary"
    );
}


export async function fetchAnomalyDetail(
    anomalyId
) {

    return apiRequest(
        `/access-monitoring/events/${anomalyId}`
    );
}


export async function fetchAnomalyEvidence(
    anomalyId
) {

    return apiRequest(
        `/access-monitoring/events/${anomalyId}/evidence`
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