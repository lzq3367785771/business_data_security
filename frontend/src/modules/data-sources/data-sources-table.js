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


function formatSourceType(value) {

    const map = {
        mysql: "MySQL",
        api: "API",
        file: "文件"
    };

    return map[value] || value || "-";
}


/*
 * 根据数据源类型显示连接位置
 */
function formatLocation(source) {

    if (
        source.source_type === "mysql"
    ) {

        if (
            source.host &&
            source.port
        ) {

            return (
                `${source.host}:` +
                `${source.port}`
            );
        }

        return (
            source.host ||
            "-"
        );
    }


    if (
        source.source_type === "api"
    ) {

        return (
            source.base_url ||
            "-"
        );
    }


    if (
        source.source_type === "file"
    ) {

        return (
            source.file_root ||
            "-"
        );
    }


    return "-";
}


/*
 * 获取所属业务系统名称
 */
function getSystemName(
    source,
    systems
) {

    const system =
        systems.find(
            item =>
                item.id ===
                source.system_id
        );


    if (!system) {

        return (
            `ID ${source.system_id}`
        );
    }


    return (
        `${system.system_name} ` +
        `(${system.system_code})`
    );
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
 * 渲染数据源表格
 *
 * callbacks:
 * {
 *     onEdit(source),
 *     onToggleStatus(source)
 * }
 */
export function renderDataSourcesTable(
    sources,
    systems,
    callbacks = {}
) {

    if (
        !sources ||
        sources.length === 0
    ) {

        const empty =
            document.createElement("div");

        empty.className =
            "empty-state";

        empty.textContent =
            "暂无数据源";

        return empty;
    }


    const wrapper =
        document.createElement("div");

    wrapper.className =
        "data-sources-table-wrapper";


    const table =
        document.createElement("table");

    table.className =
        "data-sources-table";


    // =========================
    // 表头
    // =========================

    const thead =
        document.createElement("thead");

    const headerRow =
        document.createElement("tr");


    [
        "数据源编码",
        "数据源名称",
        "所属业务系统",
        "类型",
        "运行环境",
        "数据库",
        "连接地址",
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


    sources.forEach(source => {

        const tr =
            document.createElement("tr");


        tr.appendChild(
            createCell(
                source.source_code
            )
        );


        tr.appendChild(
            createCell(
                source.source_name
            )
        );


        tr.appendChild(
            createCell(
                getSystemName(
                    source,
                    systems
                )
            )
        );


        tr.appendChild(
            createCell(
                formatSourceType(
                    source.source_type
                )
            )
        );


        tr.appendChild(
            createCell(
                formatEnvironment(
                    source.environment
                )
            )
        );


        tr.appendChild(
            createCell(
                source.database_name
            )
        );


        tr.appendChild(
            createCell(
                formatLocation(
                    source
                )
            )
        );


        // =====================
        // 状态
        // =====================

        const statusCell =
            createCell(
                formatStatus(
                    source.status
                )
            );


        statusCell.classList.add(
            source.status === "active"
                ? "data-source-status-active"
                : "data-source-status-inactive"
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
            "data-source-actions";


        const editButton =
            createActionButton(
                "编辑",
                "data-source-action-button"
            );


        const toggleButton =
            createActionButton(
                source.status === "active"
                    ? "停用"
                    : "启用",

                source.status === "active"
                    ? "data-source-action-button data-source-action-danger"
                    : "data-source-action-button data-source-action-enable"
            );


        editButton.addEventListener(
            "click",
            () => {

                if (
                    typeof callbacks.onEdit ===
                    "function"
                ) {

                    callbacks.onEdit(
                        source
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
                        source
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