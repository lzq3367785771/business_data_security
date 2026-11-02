function createCell(
    value
) {

    const td =
        document.createElement("td");

    td.textContent =
        value === null ||
        value === undefined ||
        value === ""
            ? "-"
            : String(value);

    return td;
}


function createActionButton(
    label,
    className,
    handler
) {

    const button =
        document.createElement("button");

    button.type =
        "button";

    button.className =
        className;

    button.textContent =
        label;

    button.addEventListener(
        "click",
        handler
    );

    return button;
}


export function renderAccessMonitoringTable(
    container,
    items,
    onStatusChange,
    onViewDetail
) {

    container.replaceChildren();


    if (
        !items ||
        items.length === 0
    ) {

        const empty =
            document.createElement("div");

        empty.className =
            "empty-state";

        empty.textContent =
            "暂无符合条件的异常事件";

        container.appendChild(
            empty
        );

        return;
    }


    const wrapper =
        document.createElement("div");

    wrapper.className =
        "access-monitoring-table-wrapper";


    const table =
        document.createElement("table");

    table.className =
        "access-monitoring-data-table";


    // =========================
    // 表头
    // =========================

    const headers = [
        "异常类型",
        "风险等级",
        "风险原因",
        "用户",
        "业务系统",
        "数据源",
        "访问对象",
        "访问次数",
        "敏感等级",
        "首次访问",
        "最后访问",
        "状态",
        "操作"
    ];


    const thead =
        document.createElement("thead");

    const headerRow =
        document.createElement("tr");


    for (
        const title
        of headers
    ) {

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


    // =========================
    // 表格主体
    // =========================

    const tbody =
        document.createElement("tbody");


    for (
        const item
        of items
    ) {

        const tr =
            document.createElement("tr");


        tr.appendChild(
            createCell(
                item.anomaly_label
            )
        );

        tr.appendChild(
            createCell(
                item.risk_text
            )
        );

        const riskReasonsCell =
            document.createElement("td");

        riskReasonsCell.className =
            "access-monitoring-risk-reasons";


        const riskReasonsContent =
            document.createElement("div");

        riskReasonsContent.className =
            "access-monitoring-risk-reasons-content";

        riskReasonsContent.textContent =
            item.risk_reasons_text || "-";


        riskReasonsCell.appendChild(
            riskReasonsContent
        );

        tr.appendChild(
            riskReasonsCell
        );
        tr.appendChild(
            createCell(
                item.username
            )
        );

        tr.appendChild(
            createCell(
                item.system_code
            )
        );

        tr.appendChild(
            createCell(
                item.source_code
            )
        );

        tr.appendChild(
            createCell(
                item.data_object
            )
        );

        tr.appendChild(
            createCell(
                item.access_count
            )
        );

        tr.appendChild(
            createCell(
                item.sensitivity_text
            )
        );

        tr.appendChild(
            createCell(
                item.first_access_text
            )
        );

        tr.appendChild(
            createCell(
                item.last_access_text
            )
        );

        tr.appendChild(
            createCell(
                item.status_text
            )
        );


        // =========================
        // 操作列
        // =========================

        const actionCell =
            document.createElement("td");

        actionCell.className =
            "access-monitoring-actions";

        const detailButton =
            createActionButton(
                "查看详情",
                "anomaly-action-button anomaly-detail-button",
                () =>
                    onViewDetail(
                        item
                    )
            );


        actionCell.appendChild(
            detailButton
        );



        if (
            item.status === "open"
        ) {

            const confirmButton =
                createActionButton(
                    "确认",
                    "anomaly-action-button anomaly-confirm-button",
                    () =>
                        onStatusChange(
                            item,
                            "confirmed"
                        )
                );


            const ignoreButton =
                createActionButton(
                    "忽略",
                    "anomaly-action-button anomaly-ignore-button",
                    () =>
                        onStatusChange(
                            item,
                            "ignored"
                        )
                );


            actionCell.append(
                confirmButton,
                ignoreButton
            );

        } else if (
            item.status ===
            "confirmed"
        ) {

            const resolveButton =
                createActionButton(
                    "标记已处置",
                    "anomaly-action-button anomaly-resolve-button",
                    () =>
                        onStatusChange(
                            item,
                            "resolved"
                        )
                );


            actionCell.appendChild(
                resolveButton
            );

        } else {

            // 已忽略、已处置事件
            // 保留“查看详情”按钮
        }


        tr.appendChild(
            actionCell
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