import "./audit.css";

import {
    apiRequest
} from "../../services/api.js";

import {
    renderTable
} from "../../components/table.js";


const AUDIT_COLUMNS = [
    {
        key: "created_at",
        title: "时间"
    },
    {
        key: "username",
        title: "用户"
    },
    {
        key: "action",
        title: "操作"
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
        key: "access_mode_text",
        title: "访问模式"
    },

    {
        key: "risk_text",
        title: "风险判定"
    },


    {
        key: "sensitive_fields_text",
        title: "敏感字段"
    },

    {
        key: "masked_fields_text",
        title: "脱敏字段"
    },
    {
        key: "result",
        title: "结果"
    },
    {
        key: "object_count",
        title: "数据量"
    }
];

function createSelect(
    defaultLabel
) {

    const select =
        document.createElement("select");

    select.className =
        "audit-filter-select";


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


function createAuditPage(
    content
) {

    content.replaceChildren();


    const page =
        document.createElement("div");

    page.className =
        "audit-page";

    const stats =
        document.createElement("div");

    stats.className =
        "audit-stats";


    // =========================
    // 筛选栏
    // =========================

    const toolbar =
        document.createElement("div");

    toolbar.className =
        "audit-toolbar";


    const userSelect =
        createSelect(
            "全部用户"
        );


    const actionSelect =
        createSelect(
            "全部操作"
        );


    const resultSelect =
        createSelect(
            "全部结果"
        );


    const accessModeSelect =
        createSelect(
            "全部访问模式"
        );

    const riskSelect =
        createSelect(
            "全部风险"
        );

    appendOptions(
        riskSelect,
        [
            "high",
            "medium",
            "controlled",
            "normal",
            "pending"
        ],
        value => {

            const labels = {
                high: "高风险",
                medium: "中风险",
                controlled: "受控访问",
                normal: "普通访问",
                pending: "待评估"
            };

            return labels[value];
        }
    );




    appendOptions(
        accessModeSelect,
        [
            "raw",
            "masked"
        ],
        value =>
            value === "raw"
                ? "原始访问"
                : "脱敏访问"
    );



    const resetButton =
        document.createElement("button");

    resetButton.type =
        "button";

    resetButton.className =
        "audit-reset-button";

    resetButton.textContent =
        "重置筛选";


    toolbar.append(
        userSelect,
        actionSelect,
        resultSelect,
        accessModeSelect,
        riskSelect,
        resetButton
    );


    // =========================
    // 表格区域
    // =========================

    const tableContainer =
        document.createElement("div");

    tableContainer.className =
        "audit-table-container";


    page.append(
        stats,
        toolbar,
        tableContainer
    );


    content.appendChild(
        page
    );


    return {
        stats,
        userSelect,
        actionSelect,
        resultSelect,
        accessModeSelect,
        riskSelect,
        resetButton,
        tableContainer
    };
}


function appendOptions(
    select,
    values,
    formatter = value => value
) {

    for (const value of values) {

        const option =
            document.createElement("option");

        option.value =
            String(value);

        option.textContent =
            formatter(value);


        select.appendChild(
            option
        );
    }
}


function getUniqueValues(
    items,
    key
) {

    return [
        ...new Set(
            items
                .map(
                    item =>
                        item[key]
                )
                .filter(
                    value =>
                        value !== null &&
                        value !== undefined &&
                        value !== ""
                )
        )
    ];
}



function getAuditRisk(
    item
) {

    const details =
        item.details || {};

    const sensitiveFields =
        details.sensitive_fields || [];

    const sensitiveFieldLevels =
        details.sensitive_field_levels || {};

    const levels =
        Object.values(
            sensitiveFieldLevels
        );


    if (
        item.action !==
        "READ_BUSINESS_DATA"
    ) {
        return {
            code: "other",
            text: "-"
        };
    }


    if (
        details.access_mode === "masked" &&
        sensitiveFields.length > 0
    ) {
        return {
            code: "controlled",
            text: "受控访问"
        };
    }


    if (
        details.access_mode === "raw" &&
        levels.includes("L4")
    ) {
        return {
            code: "high",
            text: "⚠ 高风险"
        };
    }


    if (
        details.access_mode === "raw" &&
        (
            levels.includes("L3") ||
            levels.includes("L2")
        )
    ) {
        return {
            code: "medium",
            text: "⚠ 中风险"
        };
    }


    if (
        details.access_mode === "raw" &&
        sensitiveFields.length > 0
    ) {
        return {
            code: "pending",
            text: "⚠ 待评估"
        };
    }


    return {
        code: "normal",
        text: "普通访问"
    };
}





function filterAuditItems(
    items,
    filters
) {

    return items.filter(
        item => {

            if (
                filters.userId &&
                String(item.user_id)
                !== filters.userId
            ) {
                return false;
            }


            if (
                filters.action &&
                item.action
                !== filters.action
            ) {
                return false;
            }


            if (
                filters.result &&
                item.result
                !== filters.result
            ) {
                return false;
            }

            if (
                filters.accessMode &&
                (
                    !item.details ||
                    item.details.access_mode
                    !== filters.accessMode
                )
            ) {
                return false;
            }

            if (
                filters.risk &&
                getAuditRisk(item).code
                !== filters.risk
            ) {
                return false;
            }

            return true;
        }
    );
}


function buildAuditDisplayItems(
    items
) {

    return items.map(
        item => {

            const details =
                item.details || {};


            let accessModeText =
                "-";

            if (
                details.access_mode
                === "raw"
            ) {

                accessModeText =
                    "原始访问";

            } else if (
                details.access_mode
                === "masked"
            ) {

                accessModeText =
                    "脱敏访问";
            }

            const sensitiveFields =
                details.sensitive_fields || [];


            const maskedFields =
                details.masked_fields || [];


            const sensitiveFieldLevels =
                details.sensitive_field_levels || {};

            const sensitivityLevels =
                Object.values(
                    sensitiveFieldLevels
                );

            const risk =
                getAuditRisk(item);
            
            const dataObject =
                (
                    details.database_name &&
                    details.table_name
                )
                    ? (
                        `${details.database_name}.` +
                        `${details.table_name}`
                    )
                    : "-";


            return {
                ...item,

                system_code:
                    details.system_code
                    || "-",

                source_code:
                    details.source_code
                    || "-",

                data_object:
                    dataObject,

                access_mode_text:
                    accessModeText,

                risk_text:
                    risk.text,

                sensitive_fields_text:
                    sensitiveFields.length > 0
                        ? sensitiveFields.join("、")
                        : (
                            details.access_mode
                                ? "无"
                                : "-"
                        ),

                masked_fields_text:
                    maskedFields.length > 0
                        ? maskedFields.join("、")
                        : (
                            details.access_mode
                                ? "无"
                                : "-"
                        )
            };
        }
    );
}



function createStatCard(
    value,
    label
) {

    const card =
        document.createElement("div");

    card.className =
        "audit-stat-card";


    const valueElement =
        document.createElement("div");

    valueElement.className =
        "audit-stat-value";

    valueElement.textContent =
        String(value);


    const labelElement =
        document.createElement("div");

    labelElement.className =
        "audit-stat-label";

    labelElement.textContent =
        label;


    card.append(
        valueElement,
        labelElement
    );


    return card;
}


function renderAuditStats(
    container,
    items
) {

    const businessAccessItems =
        items.filter(
            item =>
                item.action ===
                "READ_BUSINESS_DATA"
        );


    const highRiskCount =
        businessAccessItems.filter(
            item =>
                getAuditRisk(item).code
                === "high"
        ).length;


    const mediumRiskCount =
        businessAccessItems.filter(
            item =>
                getAuditRisk(item).code
                === "medium"
        ).length;


    const rawSensitiveCount =
        businessAccessItems.filter(
            item => {

                const details =
                    item.details || {};

                const sensitiveFields =
                    details.sensitive_fields || [];

                return (
                    details.access_mode === "raw" &&
                    sensitiveFields.length > 0
                );
            }
        ).length;


    container.replaceChildren(
        createStatCard(
            items.length,
            "审计记录总数"
        ),

        createStatCard(
            highRiskCount,
            "高风险事件"
        ),

        createStatCard(
            mediumRiskCount,
            "中风险事件"
        ),

        createStatCard(
            rawSensitiveCount,
            "原始敏感数据访问"
        )
    );
}




function renderAuditData(
    context,
    refs,
    items,
    filters
) {

    const filteredItems =
        filterAuditItems(
            items,
            filters
        );


    const displayItems =
        buildAuditDisplayItems(
            filteredItems
        );



    renderTable(
        refs.tableContainer,
        AUDIT_COLUMNS,
        displayItems
    );


    context.statusMessage.textContent =
        `共加载 ${items.length} 条审计记录，` +
        `当前显示 ${filteredItems.length} 条`;
}


export async function loadAudit(
    context
) {

    const {
        content,
        statusMessage
    } = context;


    statusMessage.textContent =
        "正在加载审计日志...";


    const data =
        await apiRequest(
            "/audit/events"
        );


    const items =
        data.items || [];


    const refs =
        createAuditPage(
            content
        );

    renderAuditStats(
        refs.stats,
        items
    );



    const filters = {
        userId: "",
        action: "",
        result: "",
        accessMode: "",
        risk: ""
    };


    // =========================
    // 用户选项
    // =========================

    const users = [
        ...new Map(
            items.map(
                item => [
                    String(item.user_id),
                    {
                        userId:
                            String(item.user_id),

                        username:
                            item.username
                            || `用户 ${item.user_id}`
                    }
                ]
            )
        ).values()
    ];


    users.sort(
        (a, b) =>
            Number(a.userId)
            - Number(b.userId)
    );


    for (const user of users) {

        const option =
            document.createElement("option");

        option.value =
            user.userId;

        option.textContent =
            `${user.username} (${user.userId})`;

        refs.userSelect.appendChild(
            option
        );
    }


    // =========================
    // 操作类型
    // =========================

    const actions =
        getUniqueValues(
            items,
            "action"
        )
            .sort();


    appendOptions(
        refs.actionSelect,
        actions
    );


    // =========================
    // 结果
    // =========================

    const results =
        getUniqueValues(
            items,
            "result"
        )
            .sort();


    appendOptions(
        refs.resultSelect,
        results
    );


    // =========================
    // 用户筛选
    // =========================

    refs.userSelect.addEventListener(
        "change",
        event => {

            filters.userId =
                event.target.value;

            renderAuditData(
                context,
                refs,
                items,
                filters
            );
        }
    );


    // =========================
    // 操作筛选
    // =========================

    refs.actionSelect.addEventListener(
        "change",
        event => {

            filters.action =
                event.target.value;

            renderAuditData(
                context,
                refs,
                items,
                filters
            );
        }
    );


    // =========================
    // 结果筛选
    // =========================

    refs.resultSelect.addEventListener(
        "change",
        event => {

            filters.result =
                event.target.value;

            renderAuditData(
                context,
                refs,
                items,
                filters
            );
        }
    );


    // =========================
    // 重置
    // =========================

    refs.resetButton.addEventListener(
        "click",
        () => {

            filters.userId = "";
            filters.action = "";
            filters.result = "";
            filters.accessMode = "";
            filters.risk = "";

            refs.userSelect.value = "";
            refs.actionSelect.value = "";
            refs.resultSelect.value = "";
            refs.accessModeSelect.value = "";
            refs.riskSelect.value = "";

            renderAuditData(
                context,
                refs,
                items,
                filters
            );
        }
    );

    refs.accessModeSelect.addEventListener(
        "change",
        event => {

            filters.accessMode =
                event.target.value;

            renderAuditData(
                context,
                refs,
                items,
                filters
            );
        }
    );

    refs.riskSelect.addEventListener(
        "change",
        event => {

            filters.risk =
                event.target.value;

            renderAuditData(
                context,
                refs,
                items,
                filters
            );
        }
    );

    // =========================
    // 初始展示
    // =========================

    renderAuditData(
        context,
        refs,
        items,
        filters
    );
}