import {
    apiRequest
} from "../../services/api.js";


/*
 * 查询凭据列表
 */
export async function fetchCredentials() {

    return apiRequest(
        "/credentials"
    );
}


/*
 * 创建新凭据
 */
export async function createCredential(
    payload
) {

    return apiRequest(
        "/credentials",
        {
            method: "POST",
            body: payload
        }
    );
}