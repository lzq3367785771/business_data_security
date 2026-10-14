import {
    apiRequest
} from "../../services/api.js";


export async function fetchBusinessPreview(
    sourceId,
    tableName,
    limit = 20
) {

    const params =
        new URLSearchParams();

    params.set(
        "limit",
        String(limit)
    );


    return apiRequest(
        `/data-access/${sourceId}` +
        `/tables/${encodeURIComponent(tableName)}` +
        `/preview?${params.toString()}`
    );
}