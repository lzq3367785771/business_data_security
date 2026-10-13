import "./data-sources.css";

import {
    fetchDataSources,
    createDataSource,
    updateDataSourceStatus
} from "./data-sources-api.js";

import {
    fetchSystems
} from "../systems/systems-api.js";

import {
    fetchCredentials
} from "../credentials/credentials-api.js";

import {
    renderDataSourcesTable
} from "./data-sources-table.js";

import {
    createDataSourceFormModal
} from "./data-sources-form.js";


/*
 * 数据源管理页面入口
 */
export async function loadDataSources({
    content,
    statusMessage
}) {

    await renderDataSourcesPage(
        content,
        statusMessage
    );
}


/*
 * 渲染数据源管理页面
 */
async function renderDataSourcesPage(
    content,
    statusMessage
) {

    content.replaceChildren();

    statusMessage.textContent =
        "正在加载数据源...";

    try {

        /*
         * 同时读取：
         * 1. 业务系统
         * 2. 数据源
         * 3. 安全凭据
         */
        const [
            systemData,
            sourceData,
            credentialData
        ] = await Promise.all([

            fetchSystems(),

            fetchDataSources(),

            fetchCredentials()
        ]);


        const systems =
            systemData?.items ?? [];


        const sources =
            sourceData?.items ?? [];


        /*
         * 数据源新增时只允许选择
         * 当前处于 active 状态的凭据。
         */
        const credentials =
            (credentialData?.items ?? [])
                .filter(
                    credential =>
                        credential.status === "active"
                );


        // =========================
        // 工具栏
        // =========================

        const toolbar =
            document.createElement("div");

        toolbar.className =
            "data-sources-toolbar";


        const toolbarTitle =
            document.createElement("div");

        toolbarTitle.className =
            "data-sources-toolbar-title";

        toolbarTitle.textContent =
            "数据源列表";


        const createButton =
            document.createElement("button");

        createButton.type =
            "button";

        createButton.className =
            "primary-button";

        createButton.textContent =
            "新增数据源";


        /*
         * 至少要有一个业务系统，
         * 才允许新增数据源。
         */
        createButton.disabled =
            systems.length === 0;


        createButton.addEventListener(
            "click",
            () => {

                openCreateDataSourceModal(
                    systems,
                    credentials,
                    content,
                    statusMessage
                );
            }
        );


        toolbar.append(
            toolbarTitle,
            createButton
        );


        content.appendChild(
            toolbar
        );


        // =========================
        // 统计区域
        // =========================

        const summary =
            document.createElement("div");

        summary.className =
            "data-sources-summary";


        const totalCard =
            createStatCard(
                "数据源",
                sources.length
            );


        const activeCount =
            sources.filter(
                source =>
                    source.status === "active"
            ).length;


        const activeCard =
            createStatCard(
                "正常运行",
                activeCount
            );


        const systemCount =
            new Set(
                sources.map(
                    source =>
                        source.system_id
                )
            ).size;


        const systemCard =
            createStatCard(
                "关联业务系统",
                systemCount
            );


        summary.append(
            totalCard,
            activeCard,
            systemCard
        );


        content.appendChild(
            summary
        );


        // =========================
        // 数据源表格
        // =========================

        const table =
            renderDataSourcesTable(
                sources,
                systems,
                {

                    /*
                     * 编辑功能稍后接入
                     */
                    onEdit(source) {

                        statusMessage.textContent =
                            `准备编辑数据源：` +
                            `${source.source_name}`;
                    },


                    /*
                     * 启用 / 停用
                     */
                    async onToggleStatus(
                        source
                    ) {

                        await handleToggleStatus(
                            source,
                            content,
                            statusMessage
                        );
                    }
                }
            );


        content.appendChild(
            table
        );


        statusMessage.textContent =
            `共加载 ${sources.length} 个数据源`;

    } catch (error) {

        statusMessage.textContent =
            `加载数据源失败：${error.message}`;
    }
}


/*
 * 打开新增数据源弹窗
 */
function openCreateDataSourceModal(
    systems,
    credentials,
    content,
    statusMessage
) {

    if (
        !systems ||
        systems.length === 0
    ) {

        statusMessage.textContent =
            "当前没有业务系统，请先创建业务系统";

        return;
    }


    createDataSourceFormModal({

        systems,

        /*
         * 把后端查询到的安全凭据
         * 交给表单。
         */
        credentials,

        title:
            "新增数据源",


        async onSubmit(
            payload
        ) {

            statusMessage.textContent =
                "正在创建数据源...";


            await createDataSource(
                payload
            );


            /*
             * 创建成功后重新读取：
             * 系统、数据源、凭据
             */
            await renderDataSourcesPage(
                content,
                statusMessage
            );


            statusMessage.textContent =
                `数据源“${payload.source_name}”创建成功`;
        }
    });
}


/*
 * 启用 / 停用数据源
 */
async function handleToggleStatus(
    source,
    content,
    statusMessage
) {

    const nextStatus =
        source.status === "active"
            ? "inactive"
            : "active";


    const actionText =
        nextStatus === "active"
            ? "启用"
            : "停用";


    const confirmed =
        window.confirm(
            `确定要${actionText}数据源` +
            `“${source.source_name}”吗？`
        );


    if (!confirmed) {
        return;
    }


    statusMessage.textContent =
        `正在${actionText}` +
        `${source.source_name}...`;


    try {

        await updateDataSourceStatus(
            source.id,
            nextStatus
        );


        await renderDataSourcesPage(
            content,
            statusMessage
        );


        statusMessage.textContent =
            `${source.source_name}` +
            `${actionText}成功`;

    } catch (error) {

        statusMessage.textContent =
            `${actionText}失败：` +
            `${error.message}`;
    }
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
        "data-sources-stat-card";


    const labelElement =
        document.createElement("span");

    labelElement.className =
        "data-sources-stat-label";

    labelElement.textContent =
        label;


    const valueElement =
        document.createElement("strong");

    valueElement.className =
        "data-sources-stat-value";

    valueElement.textContent =
        String(value);


    card.append(
        labelElement,
        valueElement
    );


    return card;
}