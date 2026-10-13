/*
 * 敏感等级显示名称
 */
function formatLevel(level) {

    const labels = {
        L1: "L1 普通",
        L2: "L2 一般敏感",
        L3: "L3 敏感",
        L4: "L4 高敏感"
    };

    return labels[level] || level;
}


/*
 * 识别方式
 */
function formatMethod(method) {

    const labels = {
        rule: "规则识别",
        content: "内容识别",
        hybrid: "融合识别",
        manual: "人工识别"
    };

    return labels[method] || method;
}


/*
 * 复核状态
 */
function formatReviewStatus(status) {

    const labels = {
        pending: "待复核",
        confirmed: "已确认",
        rejected: "已驳回"
    };

    return labels[status] || status;
}


/*
 * 创建普通单元格
 */
function createTextCell(value) {

    const td =
        document.createElement("td");

    td.textContent =
        String(value ?? "");

    return td;
}


/*
 * 敏感等级标签
 */
function createLevelCell(level) {

    const td =
        document.createElement("td");


    const badge =
        document.createElement("span");


    badge.className =
        `sensitive-level-badge sensitive-level-${level}`;


    badge.textContent =
        formatLevel(level);


    td.appendChild(
        badge
    );

    return td;
}


/*
 * 复核状态标签
 */
function createReviewStatusCell(
    status
) {

    const td =
        document.createElement("td");


    const badge =
        document.createElement("span");


    badge.className =
        `review-badge review-${status}`;


    badge.textContent =
        formatReviewStatus(status);


    td.appendChild(
        badge
    );

    return td;
}


/*
 * 创建操作按钮
 */
function createActionCell(
    item,
    onReview
) {

    const td =
        document.createElement("td");


    const group =
        document.createElement("div");

    group.className =
        "sensitive-action-group";


    // =====================
    // 确认
    // =====================

    const confirmButton =
        document.createElement("button");

    confirmButton.type =
        "button";

    confirmButton.className =
        "sensitive-action-button action-confirm";

    confirmButton.textContent =
        "确认";

    confirmButton.disabled =
        item.review_status
        === "confirmed";


    confirmButton.addEventListener(
        "click",
        () => {

            onReview(
                item,
                "confirmed"
            );
        }
    );


    // =====================
    // 驳回
    // =====================

    const rejectButton =
        document.createElement("button");

    rejectButton.type =
        "button";

    rejectButton.className =
        "sensitive-action-button action-reject";

    rejectButton.textContent =
        "驳回";

    rejectButton.disabled =
        item.review_status
        === "rejected";


    rejectButton.addEventListener(
        "click",
        () => {

            onReview(
                item,
                "rejected"
            );
        }
    );


    group.appendChild(
        confirmButton
    );

    group.appendChild(
        rejectButton
    );


    td.appendChild(
        group
    );


    return td;
}


/*
 * 渲染敏感字段表格
 */
export function renderSensitiveTable(
    container,
    rows,
    onReview
) {

    container.replaceChildren();


    if (!rows || rows.length === 0) {

        const empty =
            document.createElement("div");

        empty.className =
            "empty-state";

        empty.textContent =
            "当前条件下暂无敏感字段";

        container.appendChild(
            empty
        );

        return;
    }


    const wrapper =
        document.createElement("div");

    wrapper.className =
        "table-wrapper";


    const table =
        document.createElement("table");

    table.className =
        "sensitive-table";


    // =====================
    // 表头
    // =====================

    const thead =
        document.createElement("thead");

    const headerRow =
        document.createElement("tr");


    const headers = [
        "数据库",
        "数据表",
        "字段",
        "数据类型",
        "敏感类型",
        "敏感等级",
        "识别方式",
        "置信度",
        "复核状态",
        "操作"
    ];


    for (const title of headers) {

        const th =
            document.createElement("th");

        th.textContent =
            title;

        headerRow.appendChild(
            th
        );
    }


    thead.appendChild(
        headerRow
    );

    table.appendChild(
        thead
    );


    // =====================
    // 数据
    // =====================

    const tbody =
        document.createElement("tbody");


    for (const item of rows) {

        const tr =
            document.createElement("tr");


        tr.appendChild(
            createTextCell(
                item.database_name
            )
        );

        tr.appendChild(
            createTextCell(
                item.table_name
            )
        );

        tr.appendChild(
            createTextCell(
                item.column_name
            )
        );

        tr.appendChild(
            createTextCell(
                item.data_type
            )
        );

        tr.appendChild(
            createTextCell(
                item.sensitive_label
                || item.sensitive_type
                || "-"
            )
        );

        tr.appendChild(
            createLevelCell(
                item.sensitivity_level
            )
        );

        tr.appendChild(
            createTextCell(
                formatMethod(
                    item.detection_method
                )
            )
        );


        const confidence =
            item.confidence == null
                ? "-"
                : `${(
                    item.confidence * 100
                ).toFixed(0)}%`;


        tr.appendChild(
            createTextCell(
                confidence
            )
        );


        tr.appendChild(
            createReviewStatusCell(
                item.review_status
            )
        );


        tr.appendChild(
            createActionCell(
                item,
                onReview
            )
        );


        tbody.appendChild(
            tr
        );
    }


    table.appendChild(
        tbody
    );


    wrapper.appendChild(
        table
    );


    container.appendChild(
        wrapper
    );
}