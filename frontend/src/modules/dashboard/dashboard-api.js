import {
    apiRequest
} from "../../services/api.js";


export async function fetchDashboardSummary() {

    return apiRequest(
        "/dashboard/summary"
    );
}