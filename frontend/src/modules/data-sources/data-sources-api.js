import {
    apiRequest
} from "../../services/api.js";


/*
 * 查询数据源列表
 *
 * systemId 可选：
 * - 传入 systemId：查询某个业务系统下的数据源
 * - 不传：查询全部数据源
 */
export async function fetchDataSources(
    systemId = null
) {

    if (
        systemId !== null &&
        systemId !== undefined
    ) {

        return apiRequest(
            `/data-sources?system_id=${encodeURIComponent(systemId)}`
        );
    }


    return apiRequest(
        "/data-sources"
    );
}


/*
 * 查询单个数据源
 */
export async function fetchDataSource(
    sourceId
) {

    return apiRequest(
        `/data-sources/${sourceId}`
    );
}


/*
 * 新增数据源
 */
export async function createDataSource(
    payload
) {

    return apiRequest(
        "/data-sources",
        {
            method: "POST",
            body: payload
        }
    );
}


/*
 * 修改数据源
 */
export async function updateDataSource(
    sourceId,
    payload
) {

    return apiRequest(
        `/data-sources/${sourceId}`,
        {
            method: "PUT",
            body: payload
        }
    );
}


/*
 * 启用 / 停用数据源
 *
 * status:
 * active / inactive
 */
export async function updateDataSourceStatus(
    sourceId,
    status
) {

    return apiRequest(
        `/data-sources/${sourceId}/status`,
        {
            method: "PATCH",

            body: {
                status
            }
        }
    );
}