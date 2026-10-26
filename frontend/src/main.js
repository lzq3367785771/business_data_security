import "./styles/global.css";

import {
    apiRequest,
    setAccessToken
} from "./services/api.js";

import {
    viewRegistry
} from "./core/view-registry.js";


// =========================
// DOM
// =========================

const loginScreen =
    document.getElementById(
        "login-screen"
    );

const appScreen =
    document.getElementById(
        "app-screen"
    );

const loginForm =
    document.getElementById(
        "login-form"
    );

const loginError =
    document.getElementById(
        "login-error"
    );

const currentUser =
    document.getElementById(
        "current-user"
    );

const pageTitle =
    document.getElementById(
        "page-title"
    );

const pageDescription =
    document.getElementById(
        "page-description"
    );

const content =
    document.getElementById(
        "content"
    );

const statusMessage =
    document.getElementById(
        "status-message"
    );


// =========================
// 应用状态
// =========================

let activeView =
    "dashboard";

let currentRole =
    null;


// =========================
// 页面上下文
// =========================

function createViewContext() {

    return {
        content,
        statusMessage
    };
}


// =========================
// 角色导航控制
// =========================

function applyRoleNavigation(
    role
) {

    currentRole = role;


    document
        .querySelectorAll(
            ".nav-button"
        )
        .forEach(button => {

            const roles = (
                button.dataset.roles || ""
            )
                .split(",")
                .map(
                    item =>
                        item.trim()
                )
                .filter(Boolean);


            button.hidden =
                !roles.includes(role);
        });
}


// =========================
// 页面加载
// =========================

async function loadView(
    view
) {

    const config =
        viewRegistry[view];


    if (!config) {
        return;
    }


    activeView = view;


    pageTitle.textContent =
        config.title;

    pageDescription.textContent =
        config.description;


    statusMessage.textContent =
        "正在加载...";


    content.replaceChildren();


    document
        .querySelectorAll(
            ".nav-button"
        )
        .forEach(button => {

            button.classList.toggle(
                "active",
                button.dataset.view
                    === view
            );
        });


    try {

        await config.load(
            createViewContext()
        );

    } catch (error) {

        statusMessage.textContent =
            "请求失败";

        content.textContent =
            error.message;
    }
}


// =========================
// 登录
// =========================

loginForm.addEventListener(
    "submit",

    async event => {

        event.preventDefault();


        loginError.textContent = "";


        const username =
            document
                .getElementById(
                    "username"
                )
                .value
                .trim();


        const password =
            document
                .getElementById(
                    "password"
                )
                .value;


        const loginButton =
            document.getElementById(
                "login-button"
            );


        loginButton.disabled = true;

        loginButton.textContent =
            "正在登录...";


        try {

            const data =
                await apiRequest(
                    "/auth/login",
                    {
                        method: "POST",

                        body: {
                            username,
                            password
                        }
                    }
                );


            // 保存 JWT
            setAccessToken(
                data.access_token
            );


            // 当前用户
            currentUser.textContent =
                `${data.user.username} (${data.user.role})`;


            // 应用角色导航
            applyRoleNavigation(
                data.user.role
            );


            // 页面切换
            loginScreen.hidden =
                true;

            appScreen.hidden =
                false;


            // 清除密码
            document
                .getElementById(
                    "password"
                )
                .value = "";


            // 默认页面
            await loadView(
                "dashboard"
            );

        } catch (error) {

            loginError.textContent =
                error.message;

        } finally {

            loginButton.disabled =
                false;

            loginButton.textContent =
                "登录系统";
        }
    }
);


// =========================
// 左侧导航
// =========================

document
    .querySelectorAll(
        ".nav-button"
    )
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


// =========================
// 刷新
// =========================

document
    .getElementById(
        "refresh-button"
    )
    .addEventListener(
        "click",

        () => {

            loadView(
                activeView
            );
        }
    );


// =========================
// 退出登录
// =========================

document
    .getElementById(
        "logout-button"
    )
    .addEventListener(
        "click",

        () => {

            // 删除内存中的 Token
            setAccessToken(null);


            currentRole = null;

            currentUser.textContent =
                "";


            document
                .querySelectorAll(
                    ".nav-button"
                )
                .forEach(button => {

                    button.hidden =
                        false;

                    button.classList.toggle(
                        "active",
                        button.dataset.view ===
                            "dashboard"
                    );
                });


            activeView =
                "dashboard";


            // 返回登录页面
            appScreen.hidden =
                true;

            loginScreen.hidden =
                false;


            content.replaceChildren();

            loginForm.reset();

            loginError.textContent =
                "";

            statusMessage.textContent =
                "";
        }
    );