const API_BASE_URL = (
    import.meta.env.VITE_API_BASE_URL ||
    "http://127.0.0.1:8000"
).replace(/\/$/, "");


/*
 * JWT 先只保存在内存中。
 *
 * 优点：
 * 不会长期保存在 localStorage 中。
 *
 * 缺点：
 * 浏览器刷新后需要重新登录。
 *
 * 对当前 V1.0 开发测试来说足够。
 */
let accessToken = null;


/*
 * 设置 / 清除 JWT
 */
export function setAccessToken(token) {
    accessToken = token;
}


/*
 * 获取当前 JWT
 *
 * 后续调试时可能会用到。
 */
export function getAccessToken() {
    return accessToken;
}


/*
 * 统一 API 请求函数
 */
export async function apiRequest(
    path,
    options = {}
) {

    const {
        method = "GET",
        body = undefined
    } = options;


    const headers = {
        "Content-Type": "application/json"
    };


    /*
     * 如果已经登录，则自动携带 JWT
     */
    if (accessToken) {

        headers["Authorization"] =
            `Bearer ${accessToken}`;
    }


    let response;

    try {

        response = await fetch(
            `${API_BASE_URL}/api/v1${path}`,
            {
                method,
                headers,

                body:
                    body === undefined
                        ? undefined
                        : JSON.stringify(body)
            }
        );

    } catch (error) {

        /*
         * 常见情况：
         * 后端没有启动
         * 8000端口不可访问
         * CORS或网络错误
         */
        throw new Error(
            "无法连接后端服务，请确认 FastAPI 已在 127.0.0.1:8000 运行"
        );
    }


    /*
     * 尝试读取 JSON
     */
    let result;

    try {

        result = await response.json();

    } catch (error) {

        throw new Error(
            `后端返回了无法解析的数据，HTTP ${response.status}`
        );
    }


    /*
     * FastAPI 当前统一响应格式：
     *
     * {
     *   code: 0,
     *   message: "success",
     *   data: ...
     * }
     */
    if (
        !response.ok ||
        result.code !== 0
    ) {

        if (
            response.status === 401
        ) {
            accessToken = null;
        }


        const error =
            new Error(
                result.message ||
                `请求失败，HTTP ${response.status}`
            );


        // 保存 HTTP 状态码
        error.status =
            response.status;


        // 保存后端结构化业务异常数据
        error.data =
            result.data || null;


        // 保存 request_id，便于后续审计排查
        error.requestId =
            result.request_id || null;


        throw error;
    }


    return result.data;
}