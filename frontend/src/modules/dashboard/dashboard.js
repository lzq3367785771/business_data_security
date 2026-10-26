import "./dashboard.css";

import {
    fetchDashboardSummary
} from "./dashboard-api.js";

import {
    formatLocalTime
} from "../../utils/datetime.js";




function createCard(
    label,
    value,
    description = ""
) {

    const card =
        document.createElement("div");

    card.className =
        "dashboard-stat-card";


    const valueElement =
        document.createElement("div");

    valueElement.className =
        "dashboard-stat-value";

    valueElement.textContent =
        String(value);


    const labelElement =
        document.createElement("div");

    labelElement.className =
        "dashboard-stat-label";

    labelElement.textContent =
        label;


    const descriptionElement =
        document.createElement("div");

    descriptionElement.className =
        "dashboard-stat-description";

    descriptionElement.textContent =
        description;


    card.append(
        valueElement,
        labelElement,
        descriptionElement
    );


    return card;
}


function createSection(
    title
) {

    const section =
        document.createElement("section");

    section.className =
        "dashboard-section";


    const heading =
        document.createElement("h3");

    heading.className =
        "dashboard-section-title";

    heading.textContent =
        title;


    const grid =
        document.createElement("div");

    grid.className =
        "dashboard-card-grid";


    section.append(
        heading,
        grid
    );


    return {
        section,
        grid
    };
}


export async function loadDashboard(
    context
) {

    const {
        content,
        statusMessage
    } = context;


    content.replaceChildren();

    statusMessage.textContent =
        "正在加载安全态势...";


    const data =
        await fetchDashboardSummary();


    const securityStatus =
        createSecurityStatus(
            data.security_status
        );


    const page =
        document.createElement("div");

    page.className =
        "dashboard-page";


    // =========================
    // 数据资产
    // =========================

    const assetSection =
        createSection(
            "数据资产概况"
        );


    assetSection.grid.append(
        createCard(
            "业务系统",
            data.assets.business_systems,
            "当前已接入平台的业务系统"
        ),

        createCard(
            "数据源",
            data.assets.data_sources,
            "当前已登记并启用的数据源"
        ),

        createCard(
            "数据库",
            data.assets.databases,
            "已经同步到平台的数据库资产"
        ),

        createCard(
            "数据表",
            data.assets.tables,
            "已经同步的数据表资产"
        ),

        createCard(
            "字段",
            data.assets.columns,
            "已经同步的字段资产"
        )
    );


    // =========================
    // 敏感数据
    // =========================

    const sensitiveSection =
        createSection(
            "敏感数据概况"
        );


    sensitiveSection.grid.append(
        createCard(
            "已确认敏感字段",
            data.sensitive_data
                .confirmed_sensitive_fields,
            "已经完成人工确认的敏感字段"
        ),

        createCard(
            "L4 高敏字段",
            data.sensitive_data
                .l4_sensitive_fields,
            "当前最高敏感等级字段"
        )
    );


    // =========================
    // 风险态势
    // =========================

    const riskSection =
        createSection(
            "风险态势"
        );


    riskSection.grid.append(
        createCard(
            "异常事件总数",
            data.risks.anomaly_total,
            "平台累计识别的异常访问事件"
        ),

        createCard(
            "高风险事件",
            data.risks.high_risk_total,
            "风险等级为 HIGH 的事件"
        ),

        createCard(
            "活跃高风险",
            data.risks.active_high_risk,
            "当前仍可能触发风险控制"
        ),

        createCard(
            "待处理",
            data.risks.open,
            "尚未人工确认的异常"
        ),

        createCard(
            "已确认",
            data.risks.confirmed,
            "已确认但尚未完成处置"
        ),

        createCard(
            "已处置",
            data.risks.resolved,
            "已经完成处置的异常事件"
        )
    );


    page.append(
        securityStatus,

        assetSection.section,

        sensitiveSection.section,

        riskSection.section,

        createTrendSection(
            data.trend_7d
        ),

        createRecentAnomalies(
            data.recent_anomalies
        ),

        createRecentAccesses(
            data.recent_accesses
        )
    );


    content.appendChild(
        page
    );


    statusMessage.textContent =
        "安全态势概览加载完成";
}



function createSecurityStatus(
    status
) {

    const panel =
        document.createElement("div");

    panel.className =
        "dashboard-security-status";


    if (
        status.level === "SAFE"
    ) {

        panel.classList.add(
            "dashboard-security-safe"
        );

    } else if (
        status.level === "ATTENTION"
    ) {

        panel.classList.add(
            "dashboard-security-attention"
        );

    } else {

        panel.classList.add(
            "dashboard-security-high"
        );
    }


    const title =
        document.createElement("div");

    title.className =
        "dashboard-security-title";

    title.textContent =
        `当前总体状态：${status.label}`;


    const message =
        document.createElement("div");

    message.className =
        "dashboard-security-message";

    message.textContent =
        status.message;


    panel.append(
        title,
        message
    );


    return panel;
}


function createRecentAnomalies(
    items
) {

    const section =
        document.createElement("section");

    section.className =
        "dashboard-section";


    const title =
        document.createElement("h3");

    title.className =
        "dashboard-section-title";

    title.textContent =
        "最近异常事件";


    section.appendChild(
        title
    );


    if (
        !items ||
        items.length === 0
    ) {

        const empty =
            document.createElement("div");

        empty.className =
            "dashboard-empty";

        empty.textContent =
            "暂无异常事件";

        section.appendChild(
            empty
        );

        return section;
    }


    const wrapper =
        document.createElement("div");

    wrapper.className =
        "dashboard-table-wrapper";


    const table =
        document.createElement("table");

    table.className =
        "dashboard-anomaly-table";


    table.innerHTML = `
        <thead>
            <tr>
                <th>时间</th>
                <th>异常类型</th>
                <th>用户</th>
                <th>业务系统</th>
                <th>数据源</th>
                <th>访问对象</th>
                <th>访问次数</th>
                <th>风险等级</th>
                <th>状态</th>
            </tr>
        </thead>
    `;


    const tbody =
        document.createElement("tbody");


    const statusLabels = {
        open: "待处理",
        confirmed: "已确认",
        ignored: "已忽略",
        resolved: "已处置"
    };


    for (
        const item
        of items
    ) {

        const row =
            document.createElement("tr");


        const values = [
            formatLocalTime(
                item.last_access_at
            ),

            item.anomaly_label || "-",

            item.username || "-",

            item.system_code || "-",

            item.source_code || "-",

            item.data_object || "-",

            item.access_count ?? 0,

            item.risk_level === "HIGH"
                ? "⚠ 高风险"
                : (
                    item.risk_level || "-"
                ),

            statusLabels[
                item.status
            ] || item.status || "-"
        ];


        for (
            const value
            of values
        ) {

            const td =
                document.createElement("td");

            td.textContent =
                String(value);

            row.appendChild(
                td
            );
        }


        tbody.appendChild(
            row
        );
    }


    table.appendChild(
        tbody
    );

    wrapper.appendChild(
        table
    );

    section.appendChild(
        wrapper
    );


    return section;
}


function createRecentAccesses(
    items
) {

    const section =
        document.createElement("section");

    section.className =
        "dashboard-section";


    const title =
        document.createElement("h3");

    title.className =
        "dashboard-section-title";

    title.textContent =
        "最近业务访问";


    section.appendChild(
        title
    );


    if (
        !items ||
        items.length === 0
    ) {

        const empty =
            document.createElement("div");

        empty.className =
            "dashboard-empty";

        empty.textContent =
            "暂无业务数据访问记录";

        section.appendChild(
            empty
        );

        return section;
    }


    const wrapper =
        document.createElement("div");

    wrapper.className =
        "dashboard-table-wrapper";


    const table =
        document.createElement("table");

    table.className =
        "dashboard-access-table";


    table.innerHTML = `
        <thead>
            <tr>
                <th>时间</th>
                <th>用户</th>
                <th>业务系统</th>
                <th>数据源</th>
                <th>访问对象</th>
                <th>访问模式</th>
                <th>风险控制</th>
                <th>脱敏字段</th>
                <th>数据量</th>
                <th>结果</th>
            </tr>
        </thead>
    `;


    const tbody =
        document.createElement("tbody");


    for (
        const item
        of items
    ) {

        const row =
            document.createElement("tr");

        if (
            item.risk_control_applied
        ) {
            row.classList.add(
                "dashboard-access-risk-row"
            );
        }




        const accessModeText =
            item.access_mode === "raw"
                ? "原始访问"
                : (
                    item.access_mode === "masked"
                        ? "脱敏访问"
                        : "-"
                );


        const riskControlText =
            item.risk_control_applied
                ? "⚠ 已触发"
                : "未触发";


        const maskedFieldsText =
            (
                item.masked_fields
                && item.masked_fields.length > 0
            )
                ? item.masked_fields.join("、")
                : "无";


        const values = [
            formatLocalTime(
                item.created_at
            ),

            item.username || "-",

            item.system_code || "-",

            item.source_code || "-",

            item.data_object || "-",

            accessModeText,

            riskControlText,

            maskedFieldsText,

            item.returned_rows ?? 0,

            item.result || "-"
        ];


        for (
            const value
            of values
        ) {

            const td =
                document.createElement("td");

            td.textContent =
                String(value);

            row.appendChild(
                td
            );
        }


        tbody.appendChild(
            row
        );
    }


    table.appendChild(
        tbody
    );

    wrapper.appendChild(
        table
    );

    section.appendChild(
        wrapper
    );


    return section;
}


function createTrendSection(
    items
) {

    const section =
        document.createElement("section");

    section.className =
        "dashboard-section";


    const title =
        document.createElement("h3");

    title.className =
        "dashboard-section-title";

    title.textContent =
        "近 7 天安全趋势";


    section.appendChild(
        title
    );


    if (
        !items ||
        items.length === 0
    ) {

        const empty =
            document.createElement("div");

        empty.className =
            "dashboard-empty";

        empty.textContent =
            "暂无趋势数据";

        section.appendChild(
            empty
        );

        return section;
    }


    const trendGrid =
        document.createElement("div");

    trendGrid.className =
        "dashboard-trend-grid";


    const metrics = [
        {
            key:
                "business_accesses",

            label:
                "业务访问",

            className:
                "dashboard-trend-business"
        },

        {
            key:
                "risk_control_accesses",

            label:
                "风险联动访问",

            className:
                "dashboard-trend-risk"
        },

        {
            key:
                "anomaly_events",

            label:
                "异常事件",

            className:
                "dashboard-trend-anomaly"
        }
    ];


    for (
        const metric
        of metrics
    ) {

        const panel =
            document.createElement("div");

        panel.className =
            "dashboard-trend-panel";


        const panelTitle =
            document.createElement("div");

        panelTitle.className =
            "dashboard-trend-title";

        panelTitle.textContent =
            metric.label;


        const values =
            items.map(
                item =>
                    Number(
                        item[
                            metric.key
                        ] || 0
                    )
            );


        const maxValue =
            Math.max(
                ...values,
                1
            );


        const bars =
            document.createElement("div");

        bars.className =
            "dashboard-trend-bars";


        items.forEach(
            (
                item,
                index
            ) => {

                const barItem =
                    document.createElement(
                        "div"
                    );

                barItem.className =
                    "dashboard-trend-bar-item";


                const value =
                    values[index];


                const valueText =
                    document.createElement(
                        "div"
                    );

                valueText.className =
                    "dashboard-trend-value";

                valueText.textContent =
                    String(value);


                const track =
                    document.createElement(
                        "div"
                    );

                track.className =
                    "dashboard-trend-track";


                const bar =
                    document.createElement(
                        "div"
                    );

                bar.className =
                    `dashboard-trend-bar ${metric.className}`;


                const percentage =
                    value === 0
                        ? 0
                        : Math.max(
                            8,
                            (
                                value
                                / maxValue
                            ) * 100
                        );


                bar.style.height =
                    `${percentage}%`;


                track.appendChild(
                    bar
                );


                const date =
                    document.createElement(
                        "div"
                    );

                date.className =
                    "dashboard-trend-date";

                date.textContent =
                    item.date
                        ? item.date.slice(
                            5
                        )
                        : "-";


                barItem.append(
                    valueText,
                    track,
                    date
                );


                bars.appendChild(
                    barItem
                );
            }
        );


        panel.append(
            panelTitle,
            bars
        );


        trendGrid.appendChild(
            panel
        );
    }


    section.appendChild(
        trendGrid
    );


    return section;
}