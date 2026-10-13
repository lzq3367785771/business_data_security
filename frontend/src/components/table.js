/*
 * 通用表格组件
 *
 * container：
 * 页面内容容器
 *
 * columns：
 * [
 *   { key: "id", title: "ID" }
 * ]
 *
 * rows：
 * 后端数据数组
 */
export function renderTable(
    container,
    columns,
    rows
) {

    container.replaceChildren();

    if (!rows || rows.length === 0) {

        const empty =
            document.createElement("div");

        empty.className =
            "empty-state";

        empty.textContent =
            "暂无数据";

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


    // =========================
    // 表头
    // =========================

    const thead =
        document.createElement("thead");

    const headerRow =
        document.createElement("tr");


    for (const column of columns) {

        const th =
            document.createElement("th");

        th.textContent =
            column.title;

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


    for (const row of rows) {

        const tr =
            document.createElement("tr");


        for (const column of columns) {

            const td =
                document.createElement("td");

            td.textContent =
                String(
                    row[column.key] ?? ""
                );

            tr.appendChild(
                td
            );
        }


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