import "./data-access.css";

import {
    renderTable
} from "../../components/table.js";

import {
    fetchSystems
} from "../systems/systems-api.js";

import {
    fetchDataSources
} from "../data-sources/data-sources-api.js";

import {
    fetchAssetTree
} from "../assets/assets-api.js";

import {
    fetchBusinessPreview
} from "./data-access-api.js";


function createState() {

    return {
        systems: [],
        sources: [],
        tables: [],

        selectedSystemId: null,
        selectedSourceId: null,
        selectedTableName: null
    };
}


function createSelectField(
    labelText
) {

    const wrapper =
        document.createElement("div");

    wrapper.className =
        "data-access-select-field";


    const label =
        document.createElement("label");

    label.className =
        "data-access-select-label";

    label.textContent =
        labelText;


    const select =
        document.createElement("select");

    select.className =
        "data-access-select";


    wrapper.append(
        label,
        select
    );


    return {
        wrapper,
        select
    };
}


function createPage(
    content
) {

    content.replaceChildren();


    const page =
        document.createElement("div");

    page.className =
        "data-access-page";


    const selectors =
        document.createElement("div");

    selectors.className =
        "data-access-selectors";


    const systemField =
        createSelectField(
            "业务系统"
        );


    const sourceField =
        createSelectField(
            "数据源"
        );


    const tableField =
        createSelectField(
            "数据表"
        );


    const limitField =
        createSelectField(
            "预览行数"
        );


    for (const value of [
        5,
        10,
        20,
        50
    ]) {

        const option =
            document.createElement("option");

        option.value =
            String(value);

        option.textContent =
            `${value} 行`;

        if (value === 20) {
            option.selected = true;
        }

        limitField.select.appendChild(
            option
        );
    }


    selectors.append(
        systemField.wrapper,
        sourceField.wrapper,
        tableField.wrapper,
        limitField.wrapper
    );


    const actionRow =
        document.createElement("div");

    actionRow.className =
        "data-access-actions";


    const queryButton =
        document.createElement("button");

    queryButton.type =
        "button";

    queryButton.className =
        "primary-button";

    queryButton.textContent =
        "查询业务数据";


    const sourceInfo =
        document.createElement("div");

    sourceInfo.className =
        "data-access-info";

    sourceInfo.textContent =
        "请选择业务系统、数据源和数据表";


    actionRow.append(
        sourceInfo,
        queryButton
    );

    const securityInfo =
        document.createElement("div");

    securityInfo.className =
        "data-access-security-info";

    securityInfo.hidden = true;



    const tableContainer =
        document.createElement("div");

    tableContainer.className =
        "data-access-table-container";


    page.append(
        selectors,
        actionRow,
        securityInfo,
        tableContainer
    );

    content.appendChild(
        page
    );


    return {
        systemSelect:
            systemField.select,

        sourceSelect:
            sourceField.select,

        tableSelect:
            tableField.select,

        limitSelect:
            limitField.select,

        queryButton,
        sourceInfo,
        securityInfo,
        tableContainer
    };
}


function clearPreviewState(
    refs
) {

    // 清空上一次查询返回的数据表格
    refs.tableContainer
        .replaceChildren();


    // 隐藏上一次访问模式提示
    refs.securityInfo.hidden =
        true;


    // 清空提示文字
    refs.securityInfo.textContent =
        "";


    // 恢复默认 class
    refs.securityInfo.className =
        "data-access-security-info";
}



function renderSystemOptions(
    select,
    systems
) {

    select.replaceChildren();


    for (const system of systems) {

        const option =
            document.createElement("option");

        option.value =
            String(system.id);

        option.textContent =
            `${system.system_name} (${system.system_code})`;

        select.appendChild(
            option
        );
    }
}


function renderSourceOptions(
    select,
    sources
) {

    select.replaceChildren();


    for (const source of sources) {

        const option =
            document.createElement("option");

        option.value =
            String(source.id);

        option.textContent =
            `${source.source_name} (${source.source_code})`;

        select.appendChild(
            option
        );
    }
}


function extractTables(
    assetData
) {

    const tables = [];


    for (
        const database
        of assetData.databases || []
    ) {

        for (
            const table
            of database.tables || []
        ) {

            tables.push({
                databaseName:
                    database.database_name,

                tableName:
                    table.table_name
            });
        }
    }


    return tables;
}


function renderTableOptions(
    select,
    tables
) {

    select.replaceChildren();


    for (const table of tables) {

        const option =
            document.createElement("option");

        option.value =
            table.tableName;

        option.textContent =
            `${table.databaseName}.${table.tableName}`;

        select.appendChild(
            option
        );
    }
}


async function loadTablesForSource(
    context,
    refs,
    state
) {

    const {
        statusMessage
    } = context;


    clearPreviewState(
        refs
    );


    if (!state.selectedSourceId) {

        state.tables = [];

        renderTableOptions(
            refs.tableSelect,
            []
        );

        return;
    }


    statusMessage.textContent =
        "正在加载数据表...";


    const assetData =
        await fetchAssetTree(
            state.selectedSourceId
        );


    state.tables =
        extractTables(
            assetData
        );


    renderTableOptions(
        refs.tableSelect,
        state.tables
    );


    if (state.tables.length === 0) {

        state.selectedTableName =
            null;

        refs.sourceInfo.textContent =
            "当前数据源没有已同步的数据表";

        statusMessage.textContent =
            "当前数据源没有可访问的数据表";

        return;
    }


    state.selectedTableName =
        state.tables[0].tableName;


    refs.tableSelect.value =
        state.selectedTableName;


    refs.sourceInfo.textContent =
        `当前选择：${state.selectedTableName}`;


    statusMessage.textContent =
        `已加载 ${state.tables.length} 张可访问数据表`;
}


async function loadSourcesForSystem(
    context,
    refs,
    state,
    systemId
) {

    const {
        statusMessage
    } = context;


    clearPreviewState(
        refs
    );


    state.selectedSystemId =
        Number(systemId);


    statusMessage.textContent =
        "正在加载数据源...";


    const data =
        await fetchDataSources(
            state.selectedSystemId
        );


    state.sources =
        data.items || [];


    renderSourceOptions(
        refs.sourceSelect,
        state.sources
    );


    if (state.sources.length === 0) {

        state.selectedSourceId =
            null;

        state.tables = [];

        refs.tableSelect.replaceChildren();


        refs.sourceInfo.textContent =
            "当前业务系统暂无数据源";

        statusMessage.textContent =
            "当前业务系统暂无数据源";

        return;
    }


    state.selectedSourceId =
        state.sources[0].id;


    refs.sourceSelect.value =
        String(
            state.selectedSourceId
        );


    await loadTablesForSource(
        context,
        refs,
        state
    );
}


async function handlePreview(
    context,
    refs,
    state
) {

    const {
        statusMessage
    } = context;


    if (
        !state.selectedSourceId
        || !state.selectedTableName
    ) {

        statusMessage.textContent =
            "请先选择数据源和数据表";

        return;
    }


    // 每次重新查询前，
    // 清理上一次查询留下的结果
    clearPreviewState(
        refs
    );


    refs.queryButton.disabled =
        true;

    refs.queryButton.textContent =
        "正在查询...";


    statusMessage.textContent =
        "正在读取真实业务数据...";





    try {

        const data =
            await fetchBusinessPreview(
                state.selectedSourceId,
                state.selectedTableName,
                Number(
                    refs.limitSelect.value
                )
            );


        const columns =
            (data.columns || []).map(
                column => ({
                    key:
                        column.column_name,

                    title:
                        column.column_name
                })
            );


        refs.securityInfo.hidden =
            false;


        if (
            data.risk_control_applied &&
            data.risk_control_reason ===
                "ACTIVE_HIGH_RISK_ANOMALY"
        ) {

            const requestedLimit =
                Number(
                    data.requested_limit ??
                    refs.limitSelect.value
                );

            const effectiveLimit =
                Number(
                    data.effective_limit ??
                    data.total_returned ??
                    requestedLimit
                );


            refs.securityInfo.className =
                "data-access-security-info " +
                "data-access-security-banner-risk";


            refs.securityInfo.textContent =
                "⚠ 高风险访问限制已生效 · " +
                "处置措施：限流 + 动态脱敏 · " +
                `请求行数：${requestedLimit} · ` +
                `允许行数：${effectiveLimit}` +
                (
                    data.active_anomaly_id
                        ? ` · 关联异常：${data.active_anomaly_id}`
                        : ""
                );

        } else if (
            data.access_mode === "masked"
        ) {

            refs.securityInfo.className =
                "data-access-security-info " +
                "data-access-security-info-masked";

            refs.securityInfo.textContent =
                "当前访问模式：脱敏访问 · " +
                "当前角色按访问策略执行脱敏 · " +
                `已脱敏字段：${
                    (data.masked_fields || []).join("、")
                }`;

        } else {

            refs.securityInfo.className =
                "data-access-security-info " +
                "data-access-security-info-raw";

            refs.securityInfo.textContent =
                "当前访问模式：原始数据访问 · " +
                "当前用户具有查看完整数据权限";
        }



        renderTable(
            refs.tableContainer,
            columns,
            data.items || []
        );


        refs.sourceInfo.textContent =
            `${data.source_code} · ` +
            `${data.database_name}.${data.table_name}`;


        if (
            data.risk_action === "LIMIT"
        ) {

            statusMessage.textContent =
                `高风险访问限制已执行：` +
                `请求 ${data.requested_limit} 行，` +
                `实际返回 ${data.total_returned} 行`;

        } else {

            statusMessage.textContent =
                `真实业务数据读取成功：` +
                `返回 ${data.total_returned} 行`;
        }

    } catch (error) {

        clearPreviewState(
            refs
        );


        const errorData =
            error.data;


        // =========================
        // BLOCK：高风险访问阻断
        // =========================

        if (
            error.status === 403 &&
            errorData &&
            errorData.risk_action === "BLOCK"
        ) {

            refs.securityInfo.hidden =
                false;

            refs.securityInfo.className =
                "data-access-security-info " +
                "data-access-security-banner-risk";


            refs.securityInfo.textContent =
                "⛔ 高风险访问已阻断 · " +
                "检测到已确认的高风险异常，" +
                "系统已拒绝本次业务数据访问" +
                (
                    errorData.active_anomaly_id
                        ? ` · 关联异常：${errorData.active_anomaly_id}`
                        : ""
                );


            statusMessage.textContent =
                "业务数据访问已阻断：本次未返回任何业务数据";

            return;
        }


        // =========================
        // 普通请求错误
        // =========================

        statusMessage.textContent =
            `业务数据读取失败：${error.message}`;

    } finally {

        refs.queryButton.disabled =
            false;

        refs.queryButton.textContent =
            "查询业务数据";
    }
}


export async function loadDataAccess(
    context
) {

    const {
        content,
        statusMessage
    } = context;


    const refs =
        createPage(
            content
        );


    const state =
        createState();


    statusMessage.textContent =
        "正在加载业务系统...";


    const systemData =
        await fetchSystems();


    state.systems =
        systemData.items || [];


    renderSystemOptions(
        refs.systemSelect,
        state.systems
    );


    if (state.systems.length === 0) {

        statusMessage.textContent =
            "当前没有业务系统";

        return;
    }


    const firstSystem =
        state.systems[0];


    refs.systemSelect.value =
        String(firstSystem.id);


    refs.systemSelect.addEventListener(
        "change",
        async () => {

            await loadSourcesForSystem(
                context,
                refs,
                state,
                refs.systemSelect.value
            );
        }
    );


    refs.sourceSelect.addEventListener(
        "change",
        async () => {

            state.selectedSourceId =
                Number(
                    refs.sourceSelect.value
                );


            await loadTablesForSource(
                context,
                refs,
                state
            );
        }
    );


    refs.tableSelect.addEventListener(
        "change",
        () => {

            state.selectedTableName =
                refs.tableSelect.value;

            clearPreviewState(
                refs
            );

            refs.sourceInfo.textContent =
                `当前选择：${state.selectedTableName}`;
        }
    );


    refs.queryButton.addEventListener(
        "click",
        () => {

            handlePreview(
                context,
                refs,
                state
            );
        }
    );


    await loadSourcesForSystem(
        context,
        refs,
        state,
        firstSystem.id
    );
}

