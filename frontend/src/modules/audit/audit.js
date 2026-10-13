import {
    apiRequest
} from "../../services/api.js";

import {
    renderTable
} from "../../components/table.js";


export async function loadAudit(
    context
) {

    const {
        content,
        statusMessage
    } = context;


    const data = await apiRequest(
        "/audit/events"
    );


    renderTable(
        content,
        [
            {
                key: "created_at",
                title: "时间"
            },
            {
                key: "user_id",
                title: "用户ID"
            },
            {
                key: "action",
                title: "操作"
            },
            {
                key: "resource",
                title: "资源"
            },
            {
                key: "result",
                title: "结果"
            },
            {
                key: "policy_id",
                title: "策略ID"
            },
            {
                key: "object_count",
                title: "数据量"
            }
        ],
        data.items
    );


    statusMessage.textContent =
        `共加载 ${data.items.length} 条审计记录`;
}