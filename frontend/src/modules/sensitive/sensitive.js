import "./sensitive.css";

import {
    fetchSensitiveFields,
    reviewSensitiveField
} from "./sensitive-api.js";

import {
    renderSensitiveTable
} from "./sensitive-table.js";


/*
 * 当前页面筛选状态
 */
const filters = {

    reviewStatus: "",

    sensitivityLevel: ""
};


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
        "sensitive-stat-card";


    const valueElement =
        document.createElement("div");

    valueElement.className =
        "sensitive-stat-value";

    valueElement.textContent =
        String(value);


    const labelElement =
        document.createElement("div");

    labelElement.className =
        "sensitive-stat-label";

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


/*
 * 创建 Select
 */
function createSelect(
    options,
    value
) {

    const select =
        document.createElement("select");

    select.className =
        "sensitive-filter-select";


    for (const optionData of options) {

        const option =
            document.createElement("option");

        option.value =
            optionData.value;

        option.textContent =
            optionData.label;

        option.selected =
            optionData.value === value;

        select.appendChild(
            option
        );
    }


    return select;
}


/*
 * 页面基础结构
 */
function createSensitivePage(
    content
) {

    content.replaceChildren();


    const page =
        document.createElement("div");

    page.className =
        "sensitive-page";


    // =====================
    // 统计区域
    // =====================

    const stats =
        document.createElement("div");

    stats.className =
        "sensitive-stats";

    stats.id =
        "sensitive-stats";


    // =====================
    // 工具栏
    // =====================

    const toolbar =
        document.createElement("div");

    toolbar.className =
        "sensitive-toolbar";


    const toolbarLeft =
        document.createElement("div");

    toolbarLeft.className =
        "sensitive-toolbar-left";


    const reviewSelect =
        createSelect(
            [
                {
                    value: "",
                    label: "全部复核状态"
                },
                {
                    value: "pending",
                    label: "待复核"
                },
                {
                    value: "confirmed",
                    label: "已确认"
                },
                {
                    value: "rejected",
                    label: "已驳回"
                }
            ],
            filters.reviewStatus
        );


    reviewSelect.id =
        "sensitive-review-filter";


    const levelSelect =
        createSelect(
            [
                {
                    value: "",
                    label: "全部敏感等级"
                },
                {
                    value: "L2",
                    label: "L2 一般敏感"
                },
                {
                    value: "L3",
                    label: "L3 敏感"
                },
                {
                    value: "L4",
                    label: "L4 高敏感"
                }
            ],
            filters.sensitivityLevel
        );


    levelSelect.id =
        "sensitive-level-filter";


    toolbarLeft.appendChild(
        reviewSelect
    );

    toolbarLeft.appendChild(
        levelSelect
    );


    const resetButton =
        document.createElement("button");

    resetButton.type =
        "button";

    resetButton.className =
        "secondary-button";

    resetButton.textContent =
        "重置筛选";


    toolbar.appendChild(
        toolbarLeft
    );

    toolbar.appendChild(
        resetButton
    );


    // =====================
    // 表格容器
    // =====================

    const tableContainer =
        document.createElement("div");

    tableContainer.id =
        "sensitive-table-container";


    page.appendChild(
        stats
    );

    page.appendChild(
        toolbar
    );

    page.appendChild(
        tableContainer
    );


    content.appendChild(
        page
    );


    return {
        stats,
        tableContainer,
        reviewSelect,
        levelSelect,
        resetButton
    };
}


/*
 * 渲染统计信息
 */
function renderStats(
    container,
    rows
) {

    container.replaceChildren();


    const pending =
        rows.filter(
            item =>
                item.review_status
                === "pending"
        ).length;


    const confirmed =
        rows.filter(
            item =>
                item.review_status
                === "confirmed"
        ).length;


    const rejected =
        rows.filter(
            item =>
                item.review_status
                === "rejected"
        ).length;


    const highRisk =
        rows.filter(
            item =>
                item.sensitivity_level
                === "L4"
        ).length;


    container.appendChild(
        createStatCard(
            "敏感字段",
            rows.length
        )
    );

    container.appendChild(
        createStatCard(
            "待复核",
            pending
        )
    );

    container.appendChild(
        createStatCard(
            "已确认",
            confirmed
        )
    );

    container.appendChild(
        createStatCard(
            "L4 高敏感",
            highRisk
        )
    );


    /*
     * rejected 暂时不单独占卡片，
     * 但仍会显示在表格筛选中。
     */
    void rejected;
}


/*
 * 获取数据并刷新页面
 */
async function refreshSensitiveData(
    context,
    refs
) {

    const {
        statusMessage
    } = context;


    statusMessage.textContent =
        "正在加载敏感字段...";


    const data =
        await fetchSensitiveFields(
            filters
        );


    renderStats(
        refs.stats,
        data.items
    );


    renderSensitiveTable(
        refs.tableContainer,
        data.items,

        async (
            item,
            reviewStatus
        ) => {

            const actionText =
                reviewStatus
                === "confirmed"
                    ? "确认"
                    : "驳回";


            statusMessage.textContent =
                `正在${actionText}字段 ${item.column_name}...`;


            try {

                await reviewSensitiveField(
                    item.profile_id,
                    reviewStatus
                );


                statusMessage.textContent =
                    `字段 ${item.column_name} ${actionText}成功`;


                await refreshSensitiveData(
                    context,
                    refs
                );

            } catch (error) {

                statusMessage.textContent =
                    `${actionText}失败：${error.message}`;
            }
        }
    );


    statusMessage.textContent =
        `共加载 ${data.total} 个敏感字段`;
}


/*
 * 页面入口
 */
export async function loadSensitive(
    context
) {

    const {
        content
    } = context;


    const refs =
        createSensitivePage(
            content
        );


    refs.reviewSelect.addEventListener(
        "change",
        async event => {

            filters.reviewStatus =
                event.target.value;

            await refreshSensitiveData(
                context,
                refs
            );
        }
    );


    refs.levelSelect.addEventListener(
        "change",
        async event => {

            filters.sensitivityLevel =
                event.target.value;

            await refreshSensitiveData(
                context,
                refs
            );
        }
    );


    refs.resetButton.addEventListener(
        "click",
        async () => {

            filters.reviewStatus =
                "";

            filters.sensitivityLevel =
                "";


            refs.reviewSelect.value =
                "";

            refs.levelSelect.value =
                "";


            await refreshSensitiveData(
                context,
                refs
            );
        }
    );


    await refreshSensitiveData(
        context,
        refs
    );
}