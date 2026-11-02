import "./access-monitoring.css";

import {
    fetchAnomalyEvents,
    fetchAnomalySummary,
    fetchAnomalyDetail,
    fetchAnomalyEvidence,
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
    summary
) {

    const averageRiskScore =
        summary.average_risk_score
        ?? "-";

    const maxRiskScore =
        summary.max_risk_score
        ?? "-";


    container.replaceChildren(
        createStatCard(
            summary.total_count ?? 0,
            "异常事件总数"
        ),

        createStatCard(
            summary.high_risk_count ?? 0,
            "高风险事件"
        ),

        createStatCard(
            summary.scored_count ?? 0,
            "已评分事件"
        ),

        createStatCard(
            summary.unscored_count ?? 0,
            "未评分事件"
        ),

        createStatCard(
            averageRiskScore,
            "平均风险分"
        ),

        createStatCard(
            maxRiskScore,
            "最高风险分"
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

    const minRiskScoreSelect =
        createSelect(
            "全部风险分数"
        );


    appendOption(
        minRiskScoreSelect,
        "30",
        "≥ 30 分"
    );

    appendOption(
        minRiskScoreSelect,
        "50",
        "≥ 50 分"
    );

    appendOption(
        minRiskScoreSelect,
        "70",
        "≥ 70 分"
    );

    appendOption(
        minRiskScoreSelect,
        "90",
        "≥ 90 分"
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
        minRiskScoreSelect,
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
    "可查看异常详情，并对待处理事件进行确认、忽略或标记已处置。";

    actionPanel.append(
        actionTitle,
        actionHint
    );


    const detailPanel =
        document.createElement("div");

    detailPanel.className =
        "access-monitoring-detail-panel";

    detailPanel.hidden = true;


    const tableContainer =
        document.createElement("div");

    tableContainer.className =
        "access-monitoring-table";


    page.append(
        stats,
        toolbar,
        actionPanel,
        detailPanel,
        tableContainer
    );

    content.appendChild(
        page
    );


    return {
        stats,
        statusSelect,
        riskSelect,
        minRiskScoreSelect,
        resetButton,
        actionPanel,
        detailPanel,
        tableContainer
    };
}


function renderAnomalyDetail(
    container,
    detail,
    evidence
) {
    container.replaceChildren();

    container.hidden = false;


    const header =
        document.createElement("div");

    header.className =
        "access-monitoring-detail-header";


    const title =
        document.createElement("div");

    title.className =
        "access-monitoring-detail-title";

    title.textContent =
        "异常事件详情";


    const closeButton =
        document.createElement("button");

    closeButton.type =
        "button";

    closeButton.className =
        "access-monitoring-detail-close";

    closeButton.textContent =
        "关闭";

    closeButton.addEventListener(
        "click",
        () => {
            container.hidden = true;
        }
    );


    header.append(
        title,
        closeButton
    );


    const grid =
        document.createElement("div");

    grid.className =
        "access-monitoring-detail-grid";


    function appendDetailItem(
        label,
        value
    ) {

        const item =
            document.createElement("div");

        item.className =
            "access-monitoring-detail-item";


        const labelElement =
            document.createElement("div");

        labelElement.className =
            "access-monitoring-detail-label";

        labelElement.textContent =
            label;


        const valueElement =
            document.createElement("div");

        valueElement.className =
            "access-monitoring-detail-value";

        valueElement.textContent =
            value === null ||
            value === undefined ||
            value === ""
                ? "-"
                : String(value);


        item.append(
            labelElement,
            valueElement
        );

        grid.appendChild(
            item
        );
    }


    const statusLabels = {
        open: "待处理",
        confirmed: "已确认",
        ignored: "已忽略",
        resolved: "已处置"
    };


    appendDetailItem(
        "异常类型",
        detail.anomaly_label
    );

    appendDetailItem(
        "风险等级",
        detail.risk_level
    );

    appendDetailItem(
        "风险分数",
        detail.risk_score
    );

    appendDetailItem(
        "状态",
        statusLabels[
            detail.status
        ] || detail.status
    );

    appendDetailItem(
        "用户",
        detail.username
    );

    appendDetailItem(
        "业务系统",
        detail.system_code
    );

    appendDetailItem(
        "数据源",
        detail.source_code
    );

    appendDetailItem(
        "访问对象",
        detail.data_object
    );

    appendDetailItem(
        "访问次数",
        detail.access_count
    );

    appendDetailItem(
        "检测窗口",
        detail.window_minutes
            ? `${detail.window_minutes} 分钟`
            : "-"
    );

    appendDetailItem(
        "首次访问",
        formatTime(
            detail.first_access_at
        )
    );

    appendDetailItem(
        "最后访问",
        formatTime(
            detail.last_access_at
        )
    );


    const reasonsSection =
        document.createElement("div");

    reasonsSection.className =
        "access-monitoring-detail-section";

    const reasonsTitle =
        document.createElement("div");

    reasonsTitle.className =
        "access-monitoring-detail-section-title";

    reasonsTitle.textContent =
        "风险原因";


    const reasons =
        document.createElement("div");

    reasons.className =
        "access-monitoring-detail-list";

    reasons.textContent =
        (
            detail.risk_reasons
            || []
        ).join("；") || "-";


    reasonsSection.append(
        reasonsTitle,
        reasons
    );


    const sensitiveSection =
        document.createElement("div");

    sensitiveSection.className =
        "access-monitoring-detail-section";

    const sensitiveTitle =
        document.createElement("div");

    sensitiveTitle.className =
        "access-monitoring-detail-section-title";

    sensitiveTitle.textContent =
        "敏感数据";


    const sensitiveContent =
        document.createElement("div");

    sensitiveContent.className =
        "access-monitoring-detail-list";

    sensitiveContent.textContent =
        (
            detail.sensitive_fields
            || []
        ).join("、") || "-";


    sensitiveSection.append(
        sensitiveTitle,
        sensitiveContent
    );


    const featuresSection =
        document.createElement("div");

    featuresSection.className =
        "access-monitoring-detail-section";

    const featuresTitle =
        document.createElement("div");

    featuresTitle.className =
        "access-monitoring-detail-section-title";

    featuresTitle.textContent =
        "风险特征快照";


    const featuresContent =
        document.createElement("pre");

    featuresContent.className =
        "access-monitoring-risk-features";

    const riskFeatures =
        detail.risk_features || {};

    featuresContent.textContent =
        Object.keys(
            riskFeatures
        ).length > 0
            ? JSON.stringify(
                riskFeatures,
                null,
                2
            )
            : "暂无风险特征快照（历史事件）";


    featuresSection.append(
        featuresTitle,
        featuresContent
    );





    const timeline =
        document.createElement("div");

    timeline.className =
        "access-monitoring-evidence-timeline";


    const evidenceItems =
        evidence?.items || [];


    if (evidenceItems.length === 0) {

        const empty =
            document.createElement("div");

        empty.className =
            "access-monitoring-evidence-empty";

        empty.textContent =
            "暂无可用审计证据";

        timeline.appendChild(
            empty
        );

    } else {

        for (
            const evidenceItem
            of evidenceItems
        ) {

            const timelineItem =
                document.createElement("div");

            timelineItem.className =
                "access-monitoring-timeline-item";


            const marker =
                document.createElement("div");

            marker.className =
                "access-monitoring-timeline-marker";


            const content =
                document.createElement("div");

            content.className =
                "access-monitoring-timeline-content";


            const top =
                document.createElement("div");

            top.className =
                "access-monitoring-timeline-top";


            const time =
                document.createElement("div");

            time.className =
                "access-monitoring-timeline-time";

            time.textContent =
                formatTime(
                    evidenceItem.created_at
                );


            const result =
                document.createElement("span");

            result.className =
                "access-monitoring-timeline-result";

            result.textContent =
                evidenceItem.result || "-";


            if (
                evidenceItem.result === "ALLOW"
            ) {
                result.classList.add(
                    "is-allow"
                );
            } else {
                result.classList.add(
                    "is-deny"
                );
            }


            top.append(
                time,
                result
            );


            const summary =
                document.createElement("div");

            summary.className =
                "access-monitoring-timeline-summary";

            const accessModeText =
                evidenceItem.access_mode === "raw"
                    ? "原始数据访问"
                    : evidenceItem.access_mode === "masked"
                        ? "脱敏数据访问"
                        : evidenceItem.access_mode || "-";

            summary.textContent =
                `${evidenceItem.username || "-"} · ` +
                `${accessModeText} · ` +
                `${evidenceItem.data_object || "-"}`;


            const metadata =
                document.createElement("div");

            metadata.className =
                "access-monitoring-timeline-metadata";

            metadata.textContent =
                `${evidenceItem.action || "-"} · ` +
                `返回 ${evidenceItem.object_count ?? 0} 条`;


            const fields =
                document.createElement("div");

            fields.className =
                "access-monitoring-timeline-fields";

            const sensitiveFields =
                evidenceItem.sensitive_fields || [];

            fields.textContent =
                sensitiveFields.length > 0
                    ? `敏感字段：${sensitiveFields.join("、")}`
                    : "敏感字段：-";


            const eventId =
                document.createElement("div");

            eventId.className =
                "access-monitoring-timeline-event-id";

            eventId.textContent =
                `证据 ID：${evidenceItem.event_id}`;


            content.append(
                top,
                summary,
                metadata,
                fields,
                eventId
            );


            timelineItem.append(
                marker,
                content
            );


            timeline.appendChild(
                timelineItem
            );
        }
    }


    evidenceSection.append(
        evidenceHeader,
        timeline
    );


    container.append(
        header,
        grid,
        reasonsSection,
        sensitiveSection,
        featuresSection,
        evidenceSection
    );
}


function renderPageData(
    refs,
    items,
    filters,
    onStatusChange,
    onViewDetail
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
        onStatusChange,
        onViewDetail
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


    const [
        data,
        summary
    ] = await Promise.all([
        fetchAnomalyEvents({
            limit: 100
        }),

        fetchAnomalySummary()
    ]);


    let items =
        data.items || [];


    const filters = {
        status: "",
        riskLevel: "",
        minRiskScore: ""
    };


    renderStats(
        refs.stats,
        summary
    );


    renderPageData(
        refs,
        items,
        filters,
        handleStatusChange,
        handleViewDetail
    );


    statusMessage.textContent =
        `共加载 ${items.length} 条异常事件`;


async function handleViewDetail(
    item
) {

    statusMessage.textContent =
        "正在加载异常事件详情...";

    try {

        const detail =
            await fetchAnomalyDetail(
                item.anomaly_id
            );


        renderAnomalyDetail(
            refs.detailPanel,
            detail
        );


        statusMessage.textContent =
            "异常事件详情加载成功";

    } catch (error) {

        statusMessage.textContent =
            `异常事件详情加载失败：${error.message}`;
    }
}



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
        const [
            refreshed,
            refreshedSummary
        ] = await Promise.all([
            fetchAnomalyEvents({
                status:
                    filters.status,

                riskLevel:
                    filters.riskLevel,

                minRiskScore:
                    filters.minRiskScore,

                limit: 100
            }),

            fetchAnomalySummary()
        ]);


        items =
            refreshed.items || [];


        renderStats(
            refs.stats,
            refreshedSummary
        );




        const count =
            renderPageData(
                refs,
                items,
                filters,
                handleStatusChange,
                handleViewDetail
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
                    handleStatusChange,
                    handleViewDetail
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
                    handleStatusChange,
                    handleViewDetail
                );

            statusMessage.textContent =
                `共加载 ${items.length} 条异常事件，` +
                `当前显示 ${count} 条`;
        }
    );


    // =========================
    // 最低风险分数筛选
    // =========================

    refs.minRiskScoreSelect.addEventListener(
        "change",
        async event => {

            filters.minRiskScore =
                event.target.value;

            statusMessage.textContent =
                "正在筛选风险事件...";

            try {

                const refreshed =
                    await fetchAnomalyEvents({
                        minRiskScore:
                            filters.minRiskScore,
                        limit: 100
                    });

                items =
                    refreshed.items || [];



                const count =
                    renderPageData(
                        refs,
                        items,
                        filters,
                        handleStatusChange,
                        handleViewDetail
                    );

                statusMessage.textContent =
                    `共加载 ${items.length} 条异常事件，` +
                    `当前显示 ${count} 条`;

            } catch (error) {

                statusMessage.textContent =
                    `风险分数筛选失败：${error.message}`;
            }
        }
    );




    

    // =========================
    // 重置筛选
    // =========================

    refs.resetButton.addEventListener(
        "click",
        async () => {

            filters.status = "";
            filters.riskLevel = "";
            filters.minRiskScore = "";

            refs.statusSelect.value = "";
            refs.riskSelect.value = "";
            refs.minRiskScoreSelect.value = "";

            statusMessage.textContent =
                "正在重置筛选...";

            try {

                const refreshed =
                    await fetchAnomalyEvents({
                        limit: 100
                    });

                items =
                    refreshed.items || [];



                const count =
                    renderPageData(
                        refs,
                        items,
                        filters,
                        handleStatusChange,
                        handleViewDetail
                    );

                statusMessage.textContent =
                    `筛选已重置，共加载 ${count} 条异常事件`;

            } catch (error) {

                statusMessage.textContent =
                    `重置筛选失败：${error.message}`;
            }
        }
    );
}