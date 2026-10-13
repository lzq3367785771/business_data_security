import "./systems.css";

import {
    fetchSystems,
    createSystem,
    updateSystem,
    updateSystemStatus
} from "./systems-api.js";

import {
    renderSystemsTable
} from "./systems-table.js";

import {
    createSystemFormModal
} from "./systems-form.js";


/*
 * 业务系统管理页面入口
 */
export async function loadSystems({
    content,
    statusMessage
}) {

    await renderSystemsPage(
        content,
        statusMessage
    );
}


/*
 * 加载并渲染整个业务系统页面
 */
async function renderSystemsPage(
    content,
    statusMessage
) {

    content.replaceChildren();

    statusMessage.textContent =
        "正在加载业务系统...";


    const data =
        await fetchSystems();


    const systems =
        data.items || [];


    // =========================
    // 页面工具栏
    // =========================

    const toolbar =
        document.createElement("div");

    toolbar.className =
        "systems-toolbar";


    const toolbarTitle =
        document.createElement("div");

    toolbarTitle.className =
        "systems-toolbar-title";

    toolbarTitle.textContent =
        "业务系统列表";


    const createButton =
        document.createElement("button");

    createButton.type =
        "button";

    createButton.className =
        "primary-button";

    createButton.textContent =
        "新增业务系统";


    createButton.addEventListener(
        "click",
        () => {

            openCreateSystemModal(
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
        "systems-summary";


    const totalCard =
        createStatCard(
            "业务系统",
            systems.length
        );


    const activeCount =
        systems.filter(
            item =>
                item.status === "active"
        ).length;


    const activeCard =
        createStatCard(
            "正常运行",
            activeCount
        );


    summary.append(
        totalCard,
        activeCard
    );


    content.appendChild(
        summary
    );


    // =========================
    // 系统表格
    // =========================

    const table =
        renderSystemsTable(
            systems,
            {

                /*
                 * 编辑业务系统
                 */
                onEdit(system) {

                    openEditSystemModal(
                        system,
                        content,
                        statusMessage
                    );
                },


                /*
                 * 启用 / 停用
                 */
                async onToggleStatus(
                    system
                ) {

                    await handleToggleStatus(
                        system,
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
        `共加载 ${systems.length} 个业务系统`;
}


/*
 * 打开新增业务系统弹窗
 */
function openCreateSystemModal(
    content,
    statusMessage
) {

    createSystemFormModal({

        title:
            "新增业务系统",


        async onSubmit(
            payload
        ) {

            statusMessage.textContent =
                "正在创建业务系统...";


            await createSystem(
                payload
            );


            await renderSystemsPage(
                content,
                statusMessage
            );


            statusMessage.textContent =
                `业务系统“${payload.system_name}”创建成功`;
        }
    });
}


/*
 * 打开编辑业务系统弹窗
 */
function openEditSystemModal(
    system,
    content,
    statusMessage
) {

    createSystemFormModal({

        title:
            "编辑业务系统",

        /*
         * 将当前系统数据传入表单，
         * systems-form.js 会自动回填。
         */
        initialData:
            system,


        /*
         * 点击“保存修改”后执行
         */
        async onSubmit(
            payload
        ) {

            statusMessage.textContent =
                `正在保存 ${system.system_name}...`;


            await updateSystem(
                system.id,
                payload
            );


            await renderSystemsPage(
                content,
                statusMessage
            );


            statusMessage.textContent =
                `业务系统“${payload.system_name}”修改成功`;
        }
    });
}


/*
 * 启用 / 停用业务系统
 */
async function handleToggleStatus(
    system,
    content,
    statusMessage
) {

    const nextStatus =
        system.status === "active"
            ? "inactive"
            : "active";


    const actionText =
        nextStatus === "active"
            ? "启用"
            : "停用";


    const confirmed =
        window.confirm(
            `确定要${actionText}业务系统` +
            `“${system.system_name}”吗？`
        );


    if (!confirmed) {
        return;
    }


    statusMessage.textContent =
        `正在${actionText}` +
        `${system.system_name}...`;


    try {

        await updateSystemStatus(
            system.id,
            nextStatus
        );


        await renderSystemsPage(
            content,
            statusMessage
        );


        statusMessage.textContent =
            `${system.system_name}` +
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
        "systems-stat-card";


    const labelElement =
        document.createElement("span");

    labelElement.className =
        "systems-stat-label";

    labelElement.textContent =
        label;


    const valueElement =
        document.createElement("strong");

    valueElement.className =
        "systems-stat-value";

    valueElement.textContent =
        String(value);


    card.append(
        labelElement,
        valueElement
    );


    return card;
}