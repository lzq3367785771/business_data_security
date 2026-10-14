import "./sensitive.css";

import {
    fetchSensitiveFields,
    reviewSensitiveField
} from "./sensitive-api.js";

import {
    renderSensitiveTable
} from "./sensitive-table.js";

import {
    fetchSystems
} from "../systems/systems-api.js";

import {
    fetchDataSources
} from "../data-sources/data-sources-api.js";


/*
 * 当前页面筛选状态
 */
const filters = {

    systemId: "",

    sourceId: "",

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


function renderSystemOptions(
    select,
    systems
) {

    select.replaceChildren();

    const allOption =
        document.createElement("option");

    allOption.value = "";
    allOption.textContent =
        "全部业务系统";

    select.appendChild(allOption);


    for (const system of systems) {

        const option =
            document.createElement("option");

        option.value =
            String(system.id);

        option.textContent =
            `${system.system_name} (${system.system_code})`;

        select.appendChild(option);
    }


    select.value =
        filters.systemId;
}


function renderSourceOptions(
    select,
    sources,
    showAll = true
) {

    select.replaceChildren();


    if (showAll) {

        const allOption =
            document.createElement("option");

        allOption.value = "";
        allOption.textContent =
            "全部数据源";

        select.appendChild(allOption);
    }


    for (const source of sources) {

        const option =
            document.createElement("option");

        option.value =
            String(source.id);

        option.textContent =
            `${source.source_name} (${source.source_code})`;

        select.appendChild(option);
    }


    select.value =
        filters.sourceId;
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


    const systemSelect =
        createSelect(
            [
                {
                    value: "",
                    label: "全部业务系统"
                }
            ],
            filters.systemId
        );

    systemSelect.id =
        "sensitive-system-filter";


    const sourceSelect =
        createSelect(
            [
                {
                    value: "",
                    label: "全部数据源"
                }
            ],
            filters.sourceId
        );

    sourceSelect.id =
        "sensitive-source-filter";


    sourceSelect.id =
        "sensitive-source-filter";




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
        systemSelect
    );

    toolbarLeft.appendChild(
        sourceSelect
    );

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

        systemSelect,
        sourceSelect,

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


    const [
        systemData,
        sourceData
    ] = await Promise.all([
        fetchSystems(),
        fetchDataSources()
    ]);


    const systems =
        systemData.items || [];

    const sources =
        sourceData.items || [];


    renderSystemOptions(
        refs.systemSelect,
        systems
    );

    renderSourceOptions(
        refs.sourceSelect,
        sources,
        true
    );


refs.systemSelect.addEventListener(
    "change",
    async event => {

        filters.systemId =
            event.target.value;

        filters.sourceId =
            "";


        /*
         * 全部业务系统
         */
        if (!filters.systemId) {

            const data =
                await fetchDataSources();

            renderSourceOptions(
                refs.sourceSelect,
                data.items || [],
                true
            );


            await refreshSensitiveData(
                context,
                refs
            );

            return;
        }


        /*
         * 指定业务系统
         */
        const data =
            await fetchDataSources(
                Number(filters.systemId)
            );

        const sources =
            data.items || [];


        renderSourceOptions(
            refs.sourceSelect,
            sources,
            false
        );


        /*
         * 当前业务系统没有数据源
         */
        if (sources.length === 0) {

            refs.stats.replaceChildren();

            refs.tableContainer.replaceChildren();

            context.statusMessage.textContent =
                "当前业务系统暂无数据源";

            return;
        }


        /*
         * 默认选择该业务系统第一个数据源
         */
        filters.sourceId =
            String(sources[0].id);

        refs.sourceSelect.value =
            filters.sourceId;


        await refreshSensitiveData(
            context,
            refs
        );
    }
);

    refs.sourceSelect.addEventListener(
        "change",
        async event => {

            filters.sourceId =
                event.target.value;

            await refreshSensitiveData(
                context,
                refs
            );
        }
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

                filters.systemId =
                    "";

                filters.sourceId =
                    "";

                filters.reviewStatus =
                    "";

                filters.sensitivityLevel =
                    "";


                refs.systemSelect.value =
                    "";

                refs.reviewSelect.value =
                    "";

                refs.levelSelect.value =
                    "";


                const sourceData =
                    await fetchDataSources();

                renderSourceOptions(
                    refs.sourceSelect,
                    sourceData.items || [],
                    true
                );

                refs.sourceSelect.value =
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