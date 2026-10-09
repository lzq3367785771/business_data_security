import "./styles/global.css";

import {
    apiRequest,
    setAccessToken
} from "./services/api.js";


const loginScreen = document.getElementById("login-screen");
const appScreen = document.getElementById("app-screen");

const loginForm = document.getElementById("login-form");
const loginError = document.getElementById("login-error");

const currentUser = document.getElementById("current-user");

const pageTitle = document.getElementById("page-title");
const pageDescription = document.getElementById(
    "page-description"
);

const content = document.getElementById("content");

const statusMessage = document.getElementById(
    "status-message"
);

let activeView = "customers";

let currentRole = null;


const viewConfig = {

    customers: {
        title: "业务数据访问",
        description: "验证访问权限与动态脱敏策略"
    },

    policies: {
        title: "安全策略",
        description: "查看当前访问控制与脱敏策略"
    },

    audit: {
        title: "行为审计",
        description: "查看系统访问和策略执行记录"
    }
};

/*
 * 根据当前用户角色控制导航菜单
 *
 * 注意：
 * 这里只负责前端展示。
 *
 * 真正权限仍然由后端 Policy Engine 控制。
 */
function applyRoleNavigation(role) {

    currentRole = role;

    document
        .querySelectorAll(".nav-button")
        .forEach(button => {

            const roles = (
                button.dataset.roles || ""
            )
                .split(",")
                .map(item => item.trim())
                .filter(Boolean);

            const allowed = roles.includes(role);

            button.hidden = !allowed;
        });
}




/*
 * 创建通用表格
 *
 * 所有后端返回数据均使用 textContent，
 * 避免直接使用 innerHTML 导致 HTML 注入。
 */
function renderTable(columns, rows) {

    content.replaceChildren();

    if (!rows || rows.length === 0) {

        const empty = document.createElement("div");

        empty.className = "empty-state";
        empty.textContent = "暂无数据";

        content.appendChild(empty);

        return;
    }


    const wrapper = document.createElement("div");

    wrapper.className = "table-wrapper";


    const table = document.createElement("table");


    /*
     * 表头
     */
    const thead = document.createElement("thead");

    const headerRow = document.createElement("tr");


    for (const column of columns) {

        const th = document.createElement("th");

        th.textContent = column.title;

        headerRow.appendChild(th);
    }


    thead.appendChild(headerRow);

    table.appendChild(thead);


    /*
     * 表格主体
     */
    const tbody = document.createElement("tbody");


    for (const row of rows) {

        const tr = document.createElement("tr");


        for (const column of columns) {

            const td = document.createElement("td");

            td.textContent = String(
                row[column.key] ?? ""
            );

            tr.appendChild(td);
        }


        tbody.appendChild(tr);
    }


    table.appendChild(tbody);

    wrapper.appendChild(table);

    content.appendChild(wrapper);
}


/*
 * 加载客户数据
 */
async function loadCustomers() {

    const data = await apiRequest(
        "/customers"
    );


    renderTable(
        [
            {
                key: "id",
                title: "ID"
            },
            {
                key: "name",
                title: "姓名"
            },
            {
                key: "phone",
                title: "手机号"
            },
            {
                key: "id_card",
                title: "身份标识"
            }
        ],
        data.items
    );


    if (data.mask_fields.length > 0) {

        statusMessage.textContent =
            `脱敏策略已生效：${data.mask_fields.join("、")}`;

    } else {

        statusMessage.textContent =
            "当前用户允许查看完整演示数据";
    }
}


/*
 * 加载策略
 */
async function loadPolicies() {

    const data = await apiRequest(
        "/policies"
    );


    const rows = data.items.map(
        item => ({

            ...item,

            allowed_roles:
                item.allowed_roles.join("、"),

            mask_fields:
                item.mask_fields.join("、") || "无",

            enabled:
                item.enabled
                    ? "启用"
                    : "停用"
        })
    );


    renderTable(
        [
            {
                key: "id",
                title: "ID"
            },
            {
                key: "name",
                title: "策略名称"
            },
            {
                key: "resource",
                title: "资源"
            },
            {
                key: "allowed_roles",
                title: "适用角色"
            },
            {
                key: "mask_fields",
                title: "脱敏字段"
            },
            {
                key: "effect",
                title: "决策"
            },
            {
                key: "priority",
                title: "优先级"
            },
            {
                key: "enabled",
                title: "状态"
            }
        ],
        rows
    );


    statusMessage.textContent =
        `共加载 ${rows.length} 条安全策略`;
}


/*
 * 加载审计日志
 */
async function loadAudit() {

    const data = await apiRequest(
        "/audit/events"
    );


    renderTable(
        [
            {
                key: "created_at",
                title: "时间"
            },
            {
                key: "user_id",
                title: "用户ID"
            },
            {
                key: "action",
                title: "操作"
            },
            {
                key: "resource",
                title: "资源"
            },
            {
                key: "result",
                title: "结果"
            },
            {
                key: "policy_id",
                title: "策略ID"
            },
            {
                key: "object_count",
                title: "数据量"
            }
        ],
        data.items
    );


    statusMessage.textContent =
        `共加载 ${data.items.length} 条审计记录`;
}


/*
 * 页面切换
 */
async function loadView(view) {

    if (!viewConfig[view]) {
        return;
    }


    activeView = view;


    const config = viewConfig[view];


    pageTitle.textContent =
        config.title;

    pageDescription.textContent =
        config.description;


    statusMessage.textContent =
        "正在加载...";


    content.replaceChildren();


    document
        .querySelectorAll(".nav-button")
        .forEach(button => {

            button.classList.toggle(
                "active",
                button.dataset.view === view
            );
        });


    try {

        if (view === "customers") {

            await loadCustomers();

        } else if (view === "policies") {

            await loadPolicies();

        } else if (view === "audit") {

            await loadAudit();
        }

    } catch (error) {

        statusMessage.textContent =
            "请求失败";

        content.textContent =
            error.message;
    }
}


/*
 * 登录
 */
loginForm.addEventListener(
    "submit",
    async event => {

        event.preventDefault();


        loginError.textContent = "";


        const username = document
            .getElementById("username")
            .value
            .trim();


        const password = document
            .getElementById("password")
            .value;


        const loginButton = document
            .getElementById("login-button");


        loginButton.disabled = true;

        loginButton.textContent =
            "正在登录...";


        try {

            const data = await apiRequest(
                "/auth/login",
                {
                    method: "POST",

                    body: {
                        username,
                        password
                    }
                }
            );


            /*
             * 保存 JWT
             */
            setAccessToken(
                data.access_token
            );


            /*
             * 显示当前用户
             */
            currentUser.textContent =
                `${data.user.username} (${data.user.role})`;

            applyRoleNavigation(
                data.user.role
            );


            /*
             * 登录页隐藏
             */
            loginScreen.hidden = true;


            /*
             * 主页面显示
             */
            appScreen.hidden = false;


            /*
             * 密码输入框清空
             */
            document
                .getElementById("password")
                .value = "";


            /*
             * 默认进入客户数据页面
             */
            await loadView(
                "customers"
            );

        } catch (error) {

            loginError.textContent =
                error.message;

        } finally {

            loginButton.disabled = false;

            loginButton.textContent =
                "登录系统";
        }
    }
);


/*
 * 左侧导航栏
 */
document
    .querySelectorAll(".nav-button")
    .forEach(button => {

        button.addEventListener(
            "click",
            () => {

                loadView(
                    button.dataset.view
                );
            }
        );

    });


/*
 * 刷新
 */
document
    .getElementById("refresh-button")
    .addEventListener(
        "click",
        () => {

            loadView(activeView);

        }
    );


/*
 * 退出登录
 */
document
    .getElementById("logout-button")
    .addEventListener(
        "click",
        () => {

            /*
             * 删除前端内存中的 Token
             */
            setAccessToken(null);

            currentRole = null;

            currentUser.textContent = "";


            document
                .querySelectorAll(".nav-button")
                .forEach(button => {

                    button.hidden = false;

                    button.classList.toggle(
                        "active",
                        button.dataset.view === "customers"
                    );
                });

            activeView = "customers";




            /*
             * 隐藏后台
             */
            appScreen.hidden = true;


            /*
             * 返回登录页
             */
            loginScreen.hidden = false;


            /*
             * 清空内容
             */
            content.replaceChildren();

            loginForm.reset();

            loginError.textContent = "";

            statusMessage.textContent = "";

        }
    );