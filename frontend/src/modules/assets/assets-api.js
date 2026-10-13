import {
    apiRequest
} from "../../services/api.js";


/*
 * 获取已经同步到平台中的资产目录
 */
export async function fetchAssetTree(
    sourceId
) {

    return apiRequest(
        `/data-sources/${sourceId}/assets`
    );
}


/*
 * 测试数据源连接
 */
export async function testAssetConnection(
    sourceId
) {

    return apiRequest(
        `/data-sources/${sourceId}/test-connection`,
        {
            method: "POST"
        }
    );
}


/*
 * 扫描数据源元数据
 *
 * 只发现数据库、表、字段，
 * 不代表已经持久化到资产目录。
 */
export async function scanAssetSource(
    sourceId
) {

    return apiRequest(
        `/data-sources/${sourceId}/scan`,
        {
            method: "POST"
        }
    );
}


/*
 * 扫描并同步资产目录
 */
export async function syncAssetSource(
    sourceId
) {

    return apiRequest(
        `/data-sources/${sourceId}/sync-assets`,
        {
            method: "POST"
        }
    );
}