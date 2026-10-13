import {
    apiRequest
} from "../../services/api.js";


/*
 * 查询业务系统列表
 */
export async function fetchSystems() {

    return apiRequest(
        "/systems"
    );
}


/*
 * 查询单个业务系统
 */
export async function fetchSystem(
    systemId
) {

    return apiRequest(
        `/systems/${systemId}`
    );
}


/*
 * 创建业务系统
 */
export async function createSystem(
    payload
) {

    return apiRequest(
        "/systems",
        {
            method: "POST",
            body: payload
        }
    );
}


/*
 * 修改业务系统
 */
export async function updateSystem(
    systemId,
    payload
) {

    return apiRequest(
        `/systems/${systemId}`,
        {
            method: "PUT",
            body: payload
        }
    );
}


/*
 * 修改业务系统状态
 *
 * status:
 * active / inactive
 */
export async function updateSystemStatus(
    systemId,
    status
) {

    return apiRequest(
        `/systems/${systemId}/status`,
        {
            method: "PATCH",

            body: {
                status
            }
        }
    );
}