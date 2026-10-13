import {
    apiRequest
} from "../../services/api.js";

import {
    renderTable
} from "../../components/table.js";


export async function loadPolicies(
    context
) {

    const {
        content,
        statusMessage
    } = context;


    const data = await apiRequest(
        "/policies"
    );


    const rows = data.items.map(
        item => ({

            ...item,

            allowed_roles:
                item.allowed_roles.join("、"),

            mask_fields:
                item.mask_fields.join("、")
                || "无",

            enabled:
                item.enabled
                    ? "启用"
                    : "停用"
        })
    );


    renderTable(
        content,
        [
            {
                key: "id",
                title: "ID"
            },
            {
                key: "name",
                title: "策略名称"
            },
            {
                key: "resource",
                title: "资源"
            },
            {
                key: "allowed_roles",
                title: "适用角色"
            },
            {
                key: "mask_fields",
                title: "脱敏字段"
            },
            {
                key: "effect",
                title: "决策"
            },
            {
                key: "priority",
                title: "优先级"
            },
            {
                key: "enabled",
                title: "状态"
            }
        ],
        rows
    );


    statusMessage.textContent =
        `共加载 ${rows.length} 条安全策略`;
}