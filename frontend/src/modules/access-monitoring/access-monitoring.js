import "./access-monitoring.css";

import {
    fetchAnomalyEvents,
    updateAnomalyStatus
} from "./access-monitoring-api.js";


import {
    renderAccessMonitoringTable
} from "./access-monitoring-table.js";


const ANOMALY_COLUMNS = [
    {
        key: "anomaly_label",
        title: "异常类型"
    },
    {
        key: "risk_text",
        title: "风险等级"
    },
    {
        key: "username",
        title: "用户"
    },
    {
        key: "system_code",
        title: "业务系统"
    },
    {
        key: "source_code",
        title: "数据源"
    },
    {
        key: "data_object",
        title: "访问对象"
    },
    {
        key: "access_count",
        title: "访问次数"
    },
    {
        key: "sensitivity_text",
        title: "敏感等级"
    },
    {
        key: "first_access_text",
        title: "首次访问"
    },
    {
        key: "last_access_text",
        title: "最后访问"
    },
    {
        key: "status_text",
        title: "状态"
    }
];



function createSelect(
    defaultLabel
) {

    const select =
        document.createElement("select");

    select.className =
        "access-monitoring-filter-select";


    const option =
        document.createElement("option");

    option.value = "";
    option.textContent =
        defaultLabel;


    select.appendChild(
        option
    );


    return select;
}


function appendOption(
    select,
    value,
    label
) {

    const option =
        document.createElement("option");

    option.value =
        value;

    option.textContent =
        label;

    select.appendChild(
        option
    );
}





function createStatCard(
    value,
    label
) {

    const card =
        document.createElement("div");

    card.className =
        "access-monitoring-stat-card";


    const valueElement =
        document.createElement("div");

    valueElement.className =
        "access-monitoring-stat-value";

    valueElement.textContent =
        String(value);


    const labelElement =
        document.createElement("div");

    labelElement.className =
        "access-monitoring-stat-label";

    labelElement.textContent =
        label;


    card.append(
        valueElement,
        labelElement
    );


    return card;
}


function formatTime(
    value
) {

    if (!value) {
        return "-";
    }

    return value.replace(
        "T",
        " "
    );
}


function buildDisplayItems(
    items
) {

    return items.map(
        item => {

            let riskText =
                item.risk_level || "-";

            if (
                item.risk_level === "HIGH"
            ) {
                riskText =
                    "⚠ 高风险";

            } else if (
                item.risk_level === "MEDIUM"
            ) {
                riskText =
                    "中风险";

            } else if (
                item.risk_level === "LOW"
            ) {
                riskText =
                    "低风险";
            }


            const statusLabels = {
                open: "待处理",
                confirmed: "已确认",
                ignored: "已忽略",
                resolved: "已处置"
            };


            return {
                ...item,

                risk_text:
                    item.risk_score === null ||
                    item.risk_score === undefined
                        ? riskText
                        : `${riskText}（${item.risk_score}分）`,

                risk_reasons_text:
                    (item.risk_reasons || []).join("、") || "-",

                sensitivity_text:
                    (item.sensitivity_levels || []).join("、") || "-",

                first_access_text:
                    formatTime(item.first_access_at),

                last_access_text:
                    formatTime(item.last_access_at),

                status_text:
                    statusLabels[
                        item.status
                    ] || item.status
            };
        }
    );
}


function renderStats(
    container,
    items
) {

    const totalCount =
        items.length;


    const highRiskCount =
        items.filter(
            item =>
                item.risk_level
                === "HIGH"
        ).length;


    const openCount =
        items.filter(
            item =>
                item.status
                === "open"
        ).length;


    const confirmedCount =
        items.filter(
            item =>
                item.status
                === "confirmed"
        ).length;


    container.replaceChildren(
        createStatCard(
            totalCount,
            "异常事件总数"
        ),

        createStatCard(
            highRiskCount,
            "高风险事件"
        ),

        createStatCard(
            openCount,
            "待处理事件"
        ),

        createStatCard(
            confirmedCount,
            "已确认事件"
        )
    );
}



function filterItems(
    items,
    filters
) {

    return items.filter(
        item => {

            if (
                filters.status &&
                item.status
                !== filters.status
            ) {
                return false;
            }


            if (
                filters.riskLevel &&
                item.risk_level
                !== filters.riskLevel
            ) {
                return false;
            }


            return true;
        }
    );
}


function createPage(
    content
) {

    content.replaceChildren();


    const page =
        document.createElement("div");

    page.className =
        "access-monitoring-page";


    const stats =
        document.createElement("div");

    stats.className =
        "access-monitoring-stats";


    const toolbar =
        document.createElement("div");

    toolbar.className =
        "access-monitoring-toolbar";


    const statusSelect =
        createSelect(
            "全部状态"
        );

    appendOption(
        statusSelect,
        "open",
        "待处理"
    );

    appendOption(
        statusSelect,
        "confirmed",
        "已确认"
    );

    appendOption(
        statusSelect,
        "ignored",
        "已忽略"
    );

    appendOption(
        statusSelect,
        "resolved",
        "已处置"
    );


    const riskSelect =
        createSelect(
            "全部风险等级"
        );

    appendOption(
        riskSelect,
        "HIGH",
        "高风险"
    );

    appendOption(
        riskSelect,
        "MEDIUM",
        "中风险"
    );

    appendOption(
        riskSelect,
        "LOW",
        "低风险"
    );


    const resetButton =
        document.createElement(
            "button"
        );

    resetButton.type =
        "button";

    resetButton.className =
        "access-monitoring-reset-button";

    resetButton.textContent =
        "重置筛选";


    toolbar.append(
        statusSelect,
        riskSelect,
        resetButton
    );




    const actionPanel =
        document.createElement("div");

    actionPanel.className =
        "access-monitoring-action-panel";


    const actionTitle =
        document.createElement("div");

    actionTitle.className =
        "access-monitoring-action-title";

    actionTitle.textContent =
        "异常事件处置";


    const actionHint =
        document.createElement("div");

    actionHint.className =
        "access-monitoring-action-hint";

    actionHint.textContent =
        "点击表格中的异常事件后，可进行确认、忽略或标记已处置。";


    actionPanel.append(
        actionTitle,
        actionHint
    );


    const tableContainer =
        document.createElement("div");

    tableContainer.className =
        "access-monitoring-table";


    page.append(
        stats,
        toolbar,
        actionPanel,
        tableContainer
    );

    content.appendChild(
        page
    );


    return {
        stats,
        statusSelect,
        riskSelect,
        resetButton,
        actionPanel,
        tableContainer
    };
}



function renderPageData(
    refs,
    items,
    filters,
    onStatusChange
) {

    const filteredItems =
        filterItems(
            items,
            filters
        );


    const displayItems =
        buildDisplayItems(
            filteredItems
        );


    renderAccessMonitoringTable(
        refs.tableContainer,
        displayItems,
        onStatusChange
    );


    return filteredItems.length;
}




export async function loadAccessMonitoring(
    context
) {

    const {
        content,
        statusMessage
    } = context;


    statusMessage.textContent =
        "正在加载异常访问事件...";


    const refs =
        createPage(
            content
        );


    const data =
        await fetchAnomalyEvents({
            limit: 100
        });


    let items =
        data.items || [];


    const filters = {
        status: "",
        riskLevel: ""
    };


    renderStats(
        refs.stats,
        items
    );


    renderPageData(
        refs,
        items,
        filters,
        handleStatusChange
    );


    statusMessage.textContent =
        `共加载 ${items.length} 条异常事件`;



async function handleStatusChange(
    item,
    newStatus
) {

    const statusLabels = {
        confirmed: "确认",
        ignored: "忽略",
        resolved: "标记已处置"
    };


    const operationName =
        statusLabels[newStatus]
        || newStatus;


    const confirmed =
        window.confirm(
            `确定要将异常事件“${item.anomaly_label}”${operationName}吗？`
        );


    if (!confirmed) {
        return;
    }


    try {

        statusMessage.textContent =
            "正在更新异常事件状态...";


        await updateAnomalyStatus(
            item.anomaly_id,
            newStatus
        );


        // 更新以后重新从后端获取
        const refreshed =
            await fetchAnomalyEvents({
                limit: 100
            });


        items =
            refreshed.items || [];


        // 统计卡片重新计算
        renderStats(
            refs.stats,
            items
        );


        const count =
            renderPageData(
                refs,
                items,
                filters,
                handleStatusChange
            );


        statusMessage.textContent =
            `异常事件状态更新成功，当前显示 ${count} 条`;

    } catch (error) {

        statusMessage.textContent =
            `状态更新失败：${error.message}`;
    }
}



    // =========================
    // 状态筛选
    // =========================

    refs.statusSelect.addEventListener(
        "change",
        event => {

            filters.status =
                event.target.value;

            const count =
                renderPageData(
                    refs,
                    items,
                    filters,
                    handleStatusChange
                );

            statusMessage.textContent =
                `共加载 ${items.length} 条异常事件，` +
                `当前显示 ${count} 条`;
        }
    );


    // =========================
    // 风险等级筛选
    // =========================

    refs.riskSelect.addEventListener(
        "change",
        event => {

            filters.riskLevel =
                event.target.value;

            const count =
                renderPageData(
                    refs,
                    items,
                    filters,
                    handleStatusChange
                );

            statusMessage.textContent =
                `共加载 ${items.length} 条异常事件，` +
                `当前显示 ${count} 条`;
        }
    );


    // =========================
    // 重置筛选
    // =========================

    refs.resetButton.addEventListener(
        "click",
        () => {

            filters.status = "";
            filters.riskLevel = "";

            refs.statusSelect.value = "";
            refs.riskSelect.value = "";


            const count =
                renderPageData(
                    refs,
                    items,
                    filters,
                    handleStatusChange
                );

            statusMessage.textContent =
                `共加载 ${items.length} 条异常事件，` +
                `当前显示 ${count} 条`;
        }
    );
}