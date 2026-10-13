import {
    apiRequest
} from "../../services/api.js";

import {
    renderTable
} from "../../components/table.js";


export async function loadCustomers(
    context
) {

    const {
        content,
        statusMessage
    } = context;


    const data = await apiRequest(
        "/customers"
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
                title: "姓名"
            },
            {
                key: "phone",
                title: "手机号"
            },
            {
                key: "id_card",
                title: "身份标识"
            }
        ],
        data.items
    );


    if (data.mask_fields.length > 0) {

        statusMessage.textContent =
            `脱敏策略已生效：${data.mask_fields.join("、")}`;

    } else {

        statusMessage.textContent =
            "当前用户允许查看完整演示数据";
    }
}