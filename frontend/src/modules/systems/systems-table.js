function createCell(text) {

    const td =
        document.createElement("td");

    td.textContent =
        text === null ||
        text === undefined ||
        text === ""
            ? "-"
            : String(text);

    return td;
}


function formatEnvironment(value) {

    const map = {
        dev: "开发",
        test: "测试",
        prod: "生产"
    };

    return map[value] || value || "-";
}


function formatStatus(value) {

    return value === "active"
        ? "启用"
        : value === "inactive"
            ? "停用"
            : value || "-";
}


/*
 * 创建操作按钮
 */
function createActionButton(
    text,
    className
) {

    const button =
        document.createElement("button");

    button.type =
        "button";

    button.className =
        className;

    button.textContent =
        text;

    return button;
}


/*
 * 渲染业务系统表格
 *
 * callbacks:
 * {
 *     onEdit(system),
 *     onToggleStatus(system)
 * }
 */
export function renderSystemsTable(
    systems,
    callbacks = {}
) {

    if (
        !systems ||
        systems.length === 0
    ) {

        const empty =
            document.createElement("div");

        empty.className =
            "empty-state";

        empty.textContent =
            "暂无业务系统";

        return empty;
    }


    const wrapper =
        document.createElement("div");

    wrapper.className =
        "systems-table-wrapper";


    const table =
        document.createElement("table");

    table.className =
        "systems-table";


    // =========================
    // 表头
    // =========================

    const thead =
        document.createElement("thead");

    const headerRow =
        document.createElement("tr");


    [
        "系统编码",
        "系统名称",
        "系统类型",
        "运行环境",
        "责任部门",
        "状态",
        "操作"
    ].forEach(title => {

        const th =
            document.createElement("th");

        th.textContent =
            title;

        headerRow.appendChild(
            th
        );
    });


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


    systems.forEach(system => {

        const tr =
            document.createElement("tr");


        tr.appendChild(
            createCell(
                system.system_code
            )
        );


        tr.appendChild(
            createCell(
                system.system_name
            )
        );


        tr.appendChild(
            createCell(
                system.system_type
            )
        );


        tr.appendChild(
            createCell(
                formatEnvironment(
                    system.environment
                )
            )
        );


        tr.appendChild(
            createCell(
                system.owner_department
            )
        );


        // =====================
        // 状态
        // =====================

        const statusCell =
            createCell(
                formatStatus(
                    system.status
                )
            );

        statusCell.classList.add(
            system.status === "active"
                ? "system-status-active"
                : "system-status-inactive"
        );

        tr.appendChild(
            statusCell
        );


        // =====================
        // 操作
        // =====================

        const actionCell =
            document.createElement("td");

        actionCell.className =
            "system-actions";


        const editButton =
            createActionButton(
                "编辑",
                "system-action-button"
            );


        const toggleButton =
            createActionButton(
                system.status === "active"
                    ? "停用"
                    : "启用",
                system.status === "active"
                    ? "system-action-button system-action-danger"
                    : "system-action-button system-action-enable"
            );


        editButton.addEventListener(
            "click",
            () => {

                if (
                    typeof callbacks.onEdit ===
                    "function"
                ) {

                    callbacks.onEdit(
                        system
                    );
                }
            }
        );


        toggleButton.addEventListener(
            "click",
            () => {

                if (
                    typeof callbacks.onToggleStatus ===
                    "function"
                ) {

                    callbacks.onToggleStatus(
                        system
                    );
                }
            }
        );


        actionCell.append(
            editButton,
            toggleButton
        );


        tr.appendChild(
            actionCell
        );


        tbody.appendChild(
            tr
        );
    });


    table.appendChild(
        tbody
    );

    wrapper.appendChild(
        table
    );


    return wrapper;
}