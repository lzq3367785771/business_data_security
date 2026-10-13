/*
 * 创建普通文本节点
 */
function createText(
    className,
    value
) {

    const element =
        document.createElement("span");

    element.className =
        className;

    element.textContent =
        String(value ?? "");

    return element;
}


/*
 * 创建小标签
 */
function createBadge(
    text,
    className = ""
) {

    const badge =
        document.createElement("span");

    badge.className =
        `asset-badge ${className}`.trim();

    badge.textContent =
        text;

    return badge;
}


/*
 * 创建字段节点
 */
function createColumnNode(
    column
) {

    const row =
        document.createElement("div");

    row.className =
        "asset-column-row";


    // =====================
    // 字段名称
    // =====================

    const nameArea =
        document.createElement("div");

    nameArea.className =
        "asset-column-name";


    const icon =
        document.createElement("span");

    icon.className =
        "asset-column-icon";

    icon.textContent =
        column.is_primary_key
            ? "🔑"
            : "•";


    const name =
        createText(
            "asset-column-name-text",
            column.column_name
        );


    nameArea.appendChild(
        icon
    );

    nameArea.appendChild(
        name
    );


    // =====================
    // 字段属性
    // =====================

    const meta =
        document.createElement("div");

    meta.className =
        "asset-column-meta";


    meta.appendChild(
        createBadge(
            column.data_type,
            "asset-type-badge"
        )
    );


    if (column.is_primary_key) {

        meta.appendChild(
            createBadge(
                "主键",
                "asset-primary-badge"
            )
        );
    }


    meta.appendChild(
        createBadge(
            column.is_nullable
                ? "可空"
                : "非空",
            column.is_nullable
                ? "asset-nullable-badge"
                : "asset-not-null-badge"
        )
    );


    row.appendChild(
        nameArea
    );

    row.appendChild(
        meta
    );


    return row;
}


/*
 * 创建数据表节点
 */
function createTableNode(
    table
) {

    const details =
        document.createElement("details");

    details.className =
        "asset-table-node";

    details.open = true;


    // =====================
    // 表头
    // =====================

    const summary =
        document.createElement("summary");

    summary.className =
        "asset-table-summary";


    const left =
        document.createElement("div");

    left.className =
        "asset-tree-summary-left";


    left.appendChild(
        createText(
            "asset-table-name",
            table.table_name
        )
    );


    left.appendChild(
        createBadge(
            table.table_type
                === "BASE TABLE"
                    ? "数据表"
                    : table.table_type
        )
    );


    const right =
        document.createElement("div");

    right.className =
        "asset-tree-summary-meta";


    right.appendChild(
        createText(
            "",
            `${table.column_count} 个字段`
        )
    );


    if (
        table.row_count !== null
        && table.row_count !== undefined
    ) {

        right.appendChild(
            createText(
                "",
                `约 ${table.row_count} 行`
            )
        );
    }


    summary.appendChild(
        left
    );

    summary.appendChild(
        right
    );


    details.appendChild(
        summary
    );


    // =====================
    // 字段列表
    // =====================

    const columns =
        document.createElement("div");

    columns.className =
        "asset-columns";


    for (
        const column
        of table.columns || []
    ) {

        columns.appendChild(
            createColumnNode(
                column
            )
        );
    }


    details.appendChild(
        columns
    );


    return details;
}


/*
 * 创建数据库节点
 */
function createDatabaseNode(
    database
) {

    const details =
        document.createElement("details");

    details.className =
        "asset-database-node";

    details.open = true;


    const summary =
        document.createElement("summary");

    summary.className =
        "asset-database-summary";


    const left =
        document.createElement("div");

    left.className =
        "asset-tree-summary-left";


    const icon =
        document.createElement("span");

    icon.className =
        "asset-database-icon";

    icon.textContent =
        "DB";


    left.appendChild(
        icon
    );


    left.appendChild(
        createText(
            "asset-database-name",
            database.database_name
        )
    );


    const right =
        document.createElement("div");

    right.className =
        "asset-tree-summary-meta";


    right.appendChild(
        createText(
            "",
            `${database.table_count} 张表`
        )
    );


    summary.appendChild(
        left
    );

    summary.appendChild(
        right
    );


    details.appendChild(
        summary
    );


    const tables =
        document.createElement("div");

    tables.className =
        "asset-tables";


    for (
        const table
        of database.tables || []
    ) {

        tables.appendChild(
            createTableNode(
                table
            )
        );
    }


    details.appendChild(
        tables
    );


    return details;
}


/*
 * 渲染整个资产树
 */
export function renderAssetTree(
    container,
    databases
) {

    container.replaceChildren();


    if (
        !databases
        || databases.length === 0
    ) {

        const empty =
            document.createElement("div");

        empty.className =
            "empty-state";

        empty.textContent =
            "当前数据源尚未同步资产，请先执行同步资产";

        container.appendChild(
            empty
        );

        return;
    }


    const tree =
        document.createElement("div");

    tree.className =
        "asset-tree";


    for (
        const database
        of databases
    ) {

        tree.appendChild(
            createDatabaseNode(
                database
            )
        );
    }


    container.appendChild(
        tree
    );
}