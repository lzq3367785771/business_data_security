import "./assets.css";

import {
    fetchAssetTree,
    testAssetConnection,
    scanAssetSource,
    syncAssetSource
} from "./assets-api.js";



import {
    renderAssetTree
} from "./asset-tree.js";

import {
    fetchSystems
} from "../systems/systems-api.js";

import {
    fetchDataSources
} from "../data-sources/data-sources-api.js";


function createAssetState() {

    return {
        systems: [],
        sources: [],

        selectedSystemId: null,
        selectedSourceId: null,

        selectedSystem: null,
        selectedSource: null
    };
}



/*
 * 创建统计卡片
 */
function createStatCard(
    label,
    value
) {

    const card =
        document.createElement("div");

    card.className =
        "asset-stat-card";


    const valueElement =
        document.createElement("div");

    valueElement.className =
        "asset-stat-value";

    valueElement.textContent =
        String(value);


    const labelElement =
        document.createElement("div");

    labelElement.className =
        "asset-stat-label";

    labelElement.textContent =
        label;


    card.appendChild(
        valueElement
    );

    card.appendChild(
        labelElement
    );


    return card;
}


function createSelectField(
    labelText
) {

    const wrapper =
        document.createElement("div");

    wrapper.className =
        "asset-select-field";


    const label =
        document.createElement("label");

    label.className =
        "asset-select-label";

    label.textContent =
        labelText;


    const select =
        document.createElement("select");

    select.className =
        "asset-select";


    wrapper.append(
        label,
        select
    );


    return {
        wrapper,
        select
    };
}


/*
 * 创建工具栏按钮
 */
function createActionButton(
    text,
    className = "secondary-button"
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
 * 创建页面框架
 */
function createAssetPage(
    content
) {

    content.replaceChildren();


    const page =
        document.createElement("div");


    const selectors =
        document.createElement("div");

    selectors.className =
        "asset-selectors";


    const systemField =
        createSelectField(
            "业务系统"
        );


    const sourceField =
        createSelectField(
            "数据源"
        );


    selectors.append(
        systemField.wrapper,
        sourceField.wrapper
    );


    page.appendChild(
        selectors
    );



    page.className =
        "assets-page";


    // =====================
    // 数据源信息
    // =====================

    const sourceHeader =
        document.createElement("div");

    sourceHeader.className =
        "asset-source-header";


    const sourceInfo =
        document.createElement("div");

    sourceInfo.className =
        "asset-source-info";


    const sourceTitle =
        document.createElement("div");

    sourceTitle.className =
        "asset-source-title";

    sourceTitle.textContent =
        "请选择数据源";


    const sourceDescription =
        document.createElement("div");

    sourceDescription.className =
        "asset-source-description";

    sourceDescription.textContent =
        "请先选择业务系统和数据源";


    sourceInfo.appendChild(
        sourceTitle
    );

    sourceInfo.appendChild(
        sourceDescription
    );


    // =====================
    // 操作按钮
    // =====================

    const actions =
        document.createElement("div");

    actions.className =
        "asset-source-actions";


    const testButton =
        createActionButton(
            "测试连接"
        );


    const scanButton =
        createActionButton(
            "扫描数据源"
        );


    const syncButton =
        createActionButton(
            "同步资产",
            "primary-button"
        );


    actions.appendChild(
        testButton
    );

    actions.appendChild(
        scanButton
    );

    actions.appendChild(
        syncButton
    );


    sourceHeader.appendChild(
        sourceInfo
    );

    sourceHeader.appendChild(
        actions
    );


    // =====================
    // 统计区域
    // =====================

    const stats =
        document.createElement("div");

    stats.className =
        "asset-stats";


    // =====================
    // 操作结果
    // =====================

    const operationMessage =
        document.createElement("div");

    operationMessage.className =
        "asset-operation-message";


    // =====================
    // 资产树标题
    // =====================

    const treeHeader =
        document.createElement("div");

    treeHeader.className =
        "asset-tree-header";


    const treeTitle =
        document.createElement("h3");

    treeTitle.textContent =
        "资产目录";


    const treeDescription =
        document.createElement("span");

    treeDescription.textContent =
        "展示已经同步到平台中的数据库、数据表和字段";


    treeHeader.appendChild(
        treeTitle
    );

    treeHeader.appendChild(
        treeDescription
    );


    // =====================
    // 资产树
    // =====================

    const treeContainer =
        document.createElement("div");

    treeContainer.className =
        "asset-tree-container";


    page.appendChild(
        sourceHeader
    );

    page.appendChild(
        stats
    );

    page.appendChild(
        operationMessage
    );

    page.appendChild(
        treeHeader
    );

    page.appendChild(
        treeContainer
    );


    content.appendChild(
        page
    );


    return {
        systemSelect:
            systemField.select,

        sourceSelect:
            sourceField.select,

        sourceTitle,
        sourceDescription,

        stats,
        treeContainer,
        operationMessage,

        testButton,
        scanButton,
        syncButton
    };
}


function renderSystemOptions(
    refs,
    systems
) {

    refs.systemSelect.replaceChildren();


    for (const system of systems) {

        const option =
            document.createElement("option");

        option.value =
            String(system.id);

        option.textContent =
            `${system.system_name} (${system.system_code})`;

        refs.systemSelect.appendChild(
            option
        );
    }
}


function renderSourceOptions(
    refs,
    sources
) {

    refs.sourceSelect.replaceChildren();


    for (const source of sources) {

        const option =
            document.createElement("option");

        option.value =
            String(source.id);

        option.textContent =
            `${source.source_name} (${source.source_code})`;

        refs.sourceSelect.appendChild(
            option
        );
    }
}


function updateSourceHeader(
    refs,
    source
) {

    if (!source) {

        refs.sourceTitle.textContent =
            "暂无数据源";

        refs.sourceDescription.textContent =
            "当前业务系统下没有可用数据源";

        return;
    }


    refs.sourceTitle.textContent =
        source.source_code;


    const typeText =
        source.source_type
            ? source.source_type.toUpperCase()
            : "-";


    refs.sourceDescription.textContent =
        `${source.source_name} · ` +
        `${typeText} · ` +
        `${source.database_name || "-"} · ` +
        `数据源 ID ${source.id}`;
}


/*
 * 渲染统计信息
 */
function renderAssetStats(
    container,
    data
) {

    container.replaceChildren();


    container.appendChild(
        createStatCard(
            "当前数据源",
            1
        )
    );


    container.appendChild(
        createStatCard(
            "数据库",
            data.database_count
        )
    );


    container.appendChild(
        createStatCard(
            "数据表",
            data.table_count
        )
    );


    container.appendChild(
        createStatCard(
            "字段",
            data.column_count
        )
    );
}


/*
 * 控制按钮忙碌状态
 */
function setButtonsBusy(
    refs,
    busy
) {

    refs.testButton.disabled =
        busy;

    refs.scanButton.disabled =
        busy;

    refs.syncButton.disabled =
        busy;
}


/*
 * 加载已经同步的资产目录
 */
async function refreshAssets(
    context,
    refs,
    state
) {

    const {
        statusMessage
    } = context;


    /*
     * 当前没有选中数据源时，
     * 不发起资产目录请求。
     */
    if (!state.selectedSourceId) {

        refs.stats.replaceChildren();

        refs.treeContainer.replaceChildren();

        statusMessage.textContent =
            "当前没有可用数据源";

        return;
    }


    statusMessage.textContent =
        "正在加载资产目录...";


    const data =
        await fetchAssetTree(
            state.selectedSourceId
        );


    renderAssetStats(
        refs.stats,
        data
    );


    renderAssetTree(
        refs.treeContainer,
        data.databases
    );


    statusMessage.textContent =
        `资产目录加载完成：` +
        `${data.database_count} 个数据库，` +
        `${data.table_count} 张表，` +
        `${data.column_count} 个字段`;
}


/*
 * 测试连接
 */
async function handleTestConnection(
    context,
    refs,
    state
) {

    const {
        statusMessage
    } = context;


    if (
        !state.selectedSourceId ||
        !state.selectedSource
    ) {

        statusMessage.textContent =
            "请先选择数据源";

        return;
    }


    setButtonsBusy(
        refs,
        true
    );


    statusMessage.textContent =
        "正在测试数据源连接...";

    refs.operationMessage.textContent =
        "";


    try {

        await testAssetConnection(
            state.selectedSourceId
        );


        refs.operationMessage.textContent =
            `连接测试成功，` +
            `${state.selectedSource.source_code} ` +
            `当前可以正常访问。`;


        refs.operationMessage.className =
            "asset-operation-message asset-operation-success";


        statusMessage.textContent =
            "数据源连接正常";

    } catch (error) {

        refs.operationMessage.textContent =
            `连接测试失败：${error.message}`;


        refs.operationMessage.className =
            "asset-operation-message asset-operation-error";


        statusMessage.textContent =
            "数据源连接测试失败";

    } finally {

        setButtonsBusy(
            refs,
            false
        );
    }
}

/*
 * 扫描数据源
 */
async function handleScan(
    context,
    refs,
    state
) {

    const {
        statusMessage
    } = context;


    if (
        !state.selectedSourceId ||
        !state.selectedSource
    ) {

        statusMessage.textContent =
            "请先选择数据源";

        return;
    }


    setButtonsBusy(
        refs,
        true
    );


    statusMessage.textContent =
        `正在扫描 ` +
        `${state.selectedSource.source_code} ` +
        `元数据...`;

    refs.operationMessage.textContent =
        "";


    try {

        await scanAssetSource(
            state.selectedSourceId
        );


        refs.operationMessage.textContent =
            "扫描完成。已发现数据源当前元数据；" +
            "扫描本身不会修改平台资产目录，" +
            "如需保存最新结果请执行“同步资产”。";


        refs.operationMessage.className =
            "asset-operation-message asset-operation-success";


        statusMessage.textContent =
            "数据源扫描完成";

    } catch (error) {

        refs.operationMessage.textContent =
            `扫描失败：${error.message}`;


        refs.operationMessage.className =
            "asset-operation-message asset-operation-error";


        statusMessage.textContent =
            "数据源扫描失败";

    } finally {

        setButtonsBusy(
            refs,
            false
        );
    }
}


/*
 * 同步资产
 */
async function handleSync(
    context,
    refs,
    state
) {

    const {
        statusMessage
    } = context;


    if (
        !state.selectedSourceId ||
        !state.selectedSource
    ) {

        statusMessage.textContent =
            "请先选择数据源";

        return;
    }


    setButtonsBusy(
        refs,
        true
    );


    statusMessage.textContent =
        `正在同步 ` +
        `${state.selectedSource.source_code} ` +
        `资产目录...`;

    refs.operationMessage.textContent =
        "";


    try {

        await syncAssetSource(
            state.selectedSourceId
        );


        refs.operationMessage.textContent =
            "资产同步成功，平台资产目录已经更新。";


        refs.operationMessage.className =
            "asset-operation-message asset-operation-success";


        /*
         * 同步成功后，
         * 重新读取当前数据源资产目录。
         */
        await refreshAssets(
            context,
            refs,
            state
        );

    } catch (error) {

        refs.operationMessage.textContent =
            `资产同步失败：${error.message}`;


        refs.operationMessage.className =
            "asset-operation-message asset-operation-error";


        statusMessage.textContent =
            "资产同步失败";

    } finally {

        setButtonsBusy(
            refs,
            false
        );
    }
}


export async function loadAssets(
    context
) {

    const {
        content,
        statusMessage
    } = context;


    const state =
        createAssetState();


    const refs =
        createAssetPage(
            content
        );


    // =========================
    // 获取业务系统
    // =========================

    statusMessage.textContent =
        "正在加载业务系统...";


    const systemData =
        await fetchSystems();


    state.systems =
        systemData.items || [];


    renderSystemOptions(
        refs,
        state.systems
    );


    // =========================
    // 没有业务系统
    // =========================

    if (state.systems.length === 0) {

        statusMessage.textContent =
            "当前没有业务系统";

        updateSourceHeader(
            refs,
            null
        );

        return;
    }


    // 默认选择第一个业务系统
    const firstSystem =
        state.systems[0];


    refs.systemSelect.value =
        String(firstSystem.id);


    // =========================
    // 业务系统切换
    // =========================

    refs.systemSelect.addEventListener(
        "change",

        async () => {

            refs.operationMessage.textContent =
                "";


            await loadSourcesForSystem(
                context,
                refs,
                state,
                refs.systemSelect.value
            );
        }
    );


    // =========================
    // 数据源切换
    // =========================

    refs.sourceSelect.addEventListener(
        "change",

        async () => {

            state.selectedSourceId =
                Number(
                    refs.sourceSelect.value
                );


            state.selectedSource =
                state.sources.find(
                    item =>
                        item.id ===
                        state.selectedSourceId
                ) || null;


            updateSourceHeader(
                refs,
                state.selectedSource
            );


            refs.operationMessage.textContent =
                "";


            await refreshAssets(
                context,
                refs,
                state
            );
        }
    );


    // =========================
    // 测试连接
    // =========================

    refs.testButton.addEventListener(
        "click",

        () => {

            handleTestConnection(
                context,
                refs,
                state
            );
        }
    );


    // =========================
    // 扫描
    // =========================

    refs.scanButton.addEventListener(
        "click",

        () => {

            handleScan(
                context,
                refs,
                state
            );
        }
    );


    // =========================
    // 同步
    // =========================

    refs.syncButton.addEventListener(
        "click",

        () => {

            handleSync(
                context,
                refs,
                state
            );
        }
    );


    // =========================
    // 默认加载第一个业务系统
    // =========================

    await loadSourcesForSystem(
        context,
        refs,
        state,
        firstSystem.id
    );
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


    state.selectedSystemId =
        Number(systemId);


    state.selectedSystem =
        state.systems.find(
            item =>
                item.id ===
                state.selectedSystemId
        ) || null;


    statusMessage.textContent =
        "正在加载数据源...";


    const data =
        await fetchDataSources(
            state.selectedSystemId
        );


    state.sources =
        data.items || [];


    renderSourceOptions(
        refs,
        state.sources
    );


    if (state.sources.length === 0) {

        state.selectedSourceId =
            null;

        state.selectedSource =
            null;


        updateSourceHeader(
            refs,
            null
        );


        refs.stats.replaceChildren();

        refs.treeContainer.replaceChildren();


        statusMessage.textContent =
            "当前业务系统暂无数据源";

        return;
    }


    state.selectedSource =
        state.sources[0];

    state.selectedSourceId =
        state.selectedSource.id;


    refs.sourceSelect.value =
        String(
            state.selectedSourceId
        );


    updateSourceHeader(
        refs,
        state.selectedSource
    );


    await refreshAssets(
        context,
        refs,
        state
    );
}