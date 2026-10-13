/*
 * 数据源新增 / 编辑弹窗
 */

export function createDataSourceFormModal({
    systems = [],
    credentials = [],
    title = "新增数据源",
    initialData = null,
    onSubmit,
    onClose
}) {

    const isEdit =
        Boolean(initialData);


    // =========================
    // 遮罩
    // =========================

    const overlay =
        document.createElement("div");

    overlay.className =
        "data-source-modal-overlay";


    // =========================
    // 弹窗主体
    // =========================

    const modal =
        document.createElement("div");

    modal.className =
        "data-source-modal";


    // =========================
    // Header
    // =========================

    const header =
        document.createElement("div");

    header.className =
        "data-source-modal-header";


    const heading =
        document.createElement("h3");

    heading.textContent =
        title;


    const closeButton =
        document.createElement("button");

    closeButton.type =
        "button";

    closeButton.className =
        "data-source-modal-close";

    closeButton.textContent =
        "×";


    header.append(
        heading,
        closeButton
    );


    // =========================
    // Form
    // =========================

    const form =
        document.createElement("form");

    form.className =
        "data-source-form";


    const grid =
        document.createElement("div");

    grid.className =
        "data-source-form-grid";


    // =========================
    // 所属业务系统
    // =========================

    const systemField =
        createSelectField({
            label:
                "所属业务系统",

            value:
                initialData?.system_id ??
                systems[0]?.id ??
                "",

            options:
                systems.map(
                    system => ({
                        value:
                            system.id,

                        label:
                            `${system.system_name} ` +
                            `(${system.system_code})`
                    })
                )
        });


    // =========================
    // 数据源编码
    // =========================

    const codeField =
        createInputField({
            label:
                "数据源编码",

            placeholder:
                "例如 HR_MYSQL",

            value:
                initialData?.source_code ??
                ""
        });


    /*
     * 编辑状态不允许修改数据源编码
     */
    if (isEdit) {

        codeField.input.readOnly =
            true;

        codeField.input.classList.add(
            "data-source-form-readonly"
        );
    }


    // =========================
    // 数据源名称
    // =========================

    const nameField =
        createInputField({
            label:
                "数据源名称",

            placeholder:
                "例如 HR人力资源数据库",

            value:
                initialData?.source_name ??
                ""
        });


    // =========================
    // 数据源类型
    // =========================

    const typeField =
        createSelectField({
            label:
                "数据源类型",

            value:
                initialData?.source_type ??
                "mysql",

            options: [
                {
                    value: "mysql",
                    label: "MySQL"
                },
                {
                    value: "api",
                    label: "API"
                },
                {
                    value: "file",
                    label: "文件"
                }
            ]
        });


    // =========================
    // 环境
    // =========================

    const environmentField =
        createSelectField({
            label:
                "运行环境",

            value:
                initialData?.environment ??
                "test",

            options: [
                {
                    value: "dev",
                    label: "开发环境"
                },
                {
                    value: "test",
                    label: "测试环境"
                },
                {
                    value: "prod",
                    label: "生产环境"
                }
            ]
        });


    // =========================
    // MySQL 字段
    // =========================

    const hostField =
        createInputField({
            label:
                "Host",

            placeholder:
                "例如 127.0.0.1",

            value:
                initialData?.host ??
                ""
        });


    const portField =
        createInputField({
            label:
                "Port",

            type:
                "number",

            placeholder:
                "3306",

            value:
                initialData?.port ??
                3306
        });


    const databaseField =
        createInputField({
            label:
                "数据库名",

            placeholder:
                "例如 hr_db",

            value:
                initialData?.database_name ??
                ""
        });


    const usernameField =
        createInputField({
            label:
                "数据库用户名",

            placeholder:
                "例如 bdas_scanner",

            value:
                initialData?.username ??
                ""
        });


    // =========================
    // API 字段
    // =========================

    const baseUrlField =
        createInputField({
            label:
                "API地址",

            placeholder:
                "例如 https://api.example.com",

            value:
                initialData?.base_url ??
                ""
        });


    // =========================
    // 文件字段
    // =========================

    const fileRootField =
        createInputField({
            label:
                "文件根目录",

            placeholder:
                "例如 D:\\data\\business",

            value:
                initialData?.file_root ??
                ""
        });


    // =========================
    // 认证类型
    // =========================

    const authField =
        createSelectField({
            label:
                "认证类型",

            value:
                initialData?.auth_type ??
                "none",

            options: [
                {
                    value: "none",
                    label: "无需认证"
                },
                {
                    value: "password",
                    label: "用户名 / 密码"
                },
                {
                    value: "token",
                    label: "Token"
                },
                {
                    value: "api_key",
                    label: "API Key"
                }
            ]
        });


    // =========================
    // 安全凭据
    // =========================

    const credentialField =
        createSelectField({
            label:
                "访问凭据",

            value:
                initialData?.secret_ref ??
                "",

            options: []
        });


    // =========================
    // 描述
    // =========================

    const descriptionField =
        createTextareaField({
            label:
                "描述",

            placeholder:
                "请输入数据源说明",

            value:
                initialData?.description ??
                ""
        });


    grid.append(
        systemField.wrapper,
        codeField.wrapper,
        nameField.wrapper,
        typeField.wrapper,
        environmentField.wrapper,

        hostField.wrapper,
        portField.wrapper,
        databaseField.wrapper,
        usernameField.wrapper,

        baseUrlField.wrapper,
        fileRootField.wrapper,

        authField.wrapper,
        credentialField.wrapper,

        descriptionField.wrapper
    );


    // =========================
    // 错误提示
    // =========================

    const errorMessage =
        document.createElement("div");

    errorMessage.className =
        "data-source-form-error";


    // =========================
    // Footer
    // =========================

    const footer =
        document.createElement("div");

    footer.className =
        "data-source-modal-footer";


    const cancelButton =
        document.createElement("button");

    cancelButton.type =
        "button";

    cancelButton.className =
        "secondary-button";

    cancelButton.textContent =
        "取消";


    const submitButton =
        document.createElement("button");

    submitButton.type =
        "submit";

    submitButton.className =
        "primary-button";

    submitButton.textContent =
        isEdit
            ? "保存修改"
            : "创建数据源";


    footer.append(
        cancelButton,
        submitButton
    );


    /*
     * footer 必须放在 form 内，
     * 否则 submit 不会触发表单事件。
     */
    form.append(
        grid,
        errorMessage,
        footer
    );


    modal.append(
        header,
        form
    );


    overlay.appendChild(
        modal
    );


    document.body.appendChild(
        overlay
    );


    // =========================
    // 更新数据源类型字段
    // =========================

    function updateSourceTypeFields() {

        const sourceType =
            typeField.input.value;


        const isMysql =
            sourceType === "mysql";

        const isApi =
            sourceType === "api";

        const isFile =
            sourceType === "file";


        setVisible(
            hostField.wrapper,
            isMysql
        );

        setVisible(
            portField.wrapper,
            isMysql
        );

        setVisible(
            databaseField.wrapper,
            isMysql
        );

        setVisible(
            usernameField.wrapper,
            isMysql
        );


        setVisible(
            baseUrlField.wrapper,
            isApi
        );


        setVisible(
            fileRootField.wrapper,
            isFile
        );
    }


    // =========================
    // 根据认证类型更新凭据
    // =========================

    function updateCredentialOptions() {

        const authType =
            authField.input.value;


        /*
         * 无需认证时：
         * 不绑定凭据
         */
        if (authType === "none") {

            credentialField.input
                .replaceChildren();


            const option =
                document.createElement(
                    "option"
                );

            option.value =
                "";

            option.textContent =
                "无需绑定凭据";


            credentialField.input
                .appendChild(
                    option
                );


            credentialField.input.disabled =
                true;

            return;
        }


        credentialField.input.disabled =
            false;


        /*
         * DataSource.auth_type
         *
         * password
         * token
         * api_key
         *
         * 对应 Credential.credential_type
         *
         * mysql_password
         * api_token
         * api_key
         */
        const typeMap = {

            password:
                "mysql_password",

            token:
                "api_token",

            api_key:
                "api_key"
        };


        const expectedType =
            typeMap[authType];


        const availableCredentials =
            credentials.filter(
                credential =>
                    credential.credential_type
                    === expectedType
            );


        credentialField.input
            .replaceChildren();


        const placeholder =
            document.createElement(
                "option"
            );

        placeholder.value =
            "";


        if (
            availableCredentials.length
            === 0
        ) {

            placeholder.textContent =
                "暂无可用凭据";

        } else {

            placeholder.textContent =
                "请选择访问凭据";
        }


        credentialField.input
            .appendChild(
                placeholder
            );


        for (
            const credential
            of availableCredentials
        ) {

            const option =
                document.createElement(
                    "option"
                );


            option.value =
                credential.credential_key;


            option.textContent =
                `${credential.credential_name} ` +
                `(${credential.credential_key})`;


            credentialField.input
                .appendChild(
                    option
                );
        }


        /*
         * 编辑时恢复原凭据
         */
        if (
            initialData?.secret_ref
        ) {

            credentialField.input.value =
                initialData.secret_ref;
        }
    }


    // =========================
    // 事件
    // =========================

    typeField.input.addEventListener(
        "change",
        updateSourceTypeFields
    );


    authField.input.addEventListener(
        "change",
        updateCredentialOptions
    );


    closeButton.addEventListener(
        "click",
        closeModal
    );


    cancelButton.addEventListener(
        "click",
        closeModal
    );


    /*
     * 点击遮罩关闭
     */
    overlay.addEventListener(
        "click",
        event => {

            if (
                event.target === overlay
            ) {

                closeModal();
            }
        }
    );


    // =========================
    // 提交
    // =========================

    form.addEventListener(
        "submit",
        async event => {

            event.preventDefault();

            errorMessage.textContent =
                "";


            const systemId =
                Number(
                    systemField.input.value
                );


            const sourceCode =
                codeField.input.value
                    .trim()
                    .toUpperCase();


            const sourceName =
                nameField.input.value
                    .trim();


            const sourceType =
                typeField.input.value;


            const authType =
                authField.input.value;


            // =====================
            // 基础校验
            // =====================

            if (!systemId) {

                errorMessage.textContent =
                    "请选择所属业务系统";

                return;
            }


            if (!sourceCode) {

                errorMessage.textContent =
                    "请输入数据源编码";

                return;
            }


            if (!sourceName) {

                errorMessage.textContent =
                    "请输入数据源名称";

                return;
            }


            // =====================
            // MySQL 校验
            // =====================

            if (
                sourceType === "mysql"
            ) {

                if (
                    !hostField.input.value
                        .trim()
                ) {

                    errorMessage.textContent =
                        "请输入 MySQL Host";

                    return;
                }


                if (
                    !portField.input.value
                ) {

                    errorMessage.textContent =
                        "请输入 MySQL Port";

                    return;
                }


                if (
                    !databaseField.input.value
                        .trim()
                ) {

                    errorMessage.textContent =
                        "请输入数据库名";

                    return;
                }
            }


            // =====================
            // API 校验
            // =====================

            if (
                sourceType === "api" &&
                !baseUrlField.input.value
                    .trim()
            ) {

                errorMessage.textContent =
                    "请输入 API 地址";

                return;
            }


            // =====================
            // 文件校验
            // =====================

            if (
                sourceType === "file" &&
                !fileRootField.input.value
                    .trim()
            ) {

                errorMessage.textContent =
                    "请输入文件根目录";

                return;
            }


            // =====================
            // 凭据校验
            // =====================

            if (
                authType !== "none" &&
                !credentialField.input.value
            ) {

                errorMessage.textContent =
                    "请选择访问凭据";

                return;
            }


            // =====================
            // Payload
            // =====================

            const payload = {

                system_id:
                    systemId,

                source_code:
                    sourceCode,

                source_name:
                    sourceName,

                source_type:
                    sourceType,

                environment:
                    environmentField
                        .input
                        .value,


                host:
                    sourceType === "mysql"
                        ? emptyToNull(
                            hostField
                                .input
                                .value
                        )
                        : null,


                port:
                    sourceType === "mysql"
                        ? numberOrNull(
                            portField
                                .input
                                .value
                        )
                        : null,


                database_name:
                    sourceType === "mysql"
                        ? emptyToNull(
                            databaseField
                                .input
                                .value
                        )
                        : null,


                username:
                    sourceType === "mysql"
                        ? emptyToNull(
                            usernameField
                                .input
                                .value
                        )
                        : null,


                base_url:
                    sourceType === "api"
                        ? emptyToNull(
                            baseUrlField
                                .input
                                .value
                        )
                        : null,


                file_root:
                    sourceType === "file"
                        ? emptyToNull(
                            fileRootField
                                .input
                                .value
                        )
                        : null,


                auth_type:
                    authType,


                /*
                 * 这里只保存凭据唯一标识。
                 *
                 * 不保存密码。
                 */
                secret_ref:
                    authType === "none"
                        ? null
                        : emptyToNull(
                            credentialField
                                .input
                                .value
                        ),


                description:
                    emptyToNull(
                        descriptionField
                            .input
                            .value
                    )
            };


            submitButton.disabled =
                true;


            submitButton.textContent =
                isEdit
                    ? "正在保存..."
                    : "正在创建...";


            try {

                await onSubmit?.(
                    payload
                );


                closeModal();

            } catch (error) {

                errorMessage.textContent =
                    error.message ||
                    "操作失败";


                submitButton.disabled =
                    false;


                submitButton.textContent =
                    isEdit
                        ? "保存修改"
                        : "创建数据源";
            }
        }
    );


    // =========================
    // 初始化
    // =========================

    updateSourceTypeFields();

    updateCredentialOptions();


    // =========================
    // 关闭
    // =========================

    function closeModal() {

        overlay.remove();

        onClose?.();
    }
}


/*
 * 输入框
 */
function createInputField({
    label,
    type = "text",
    placeholder = "",
    value = ""
}) {

    const wrapper =
        createFieldWrapper(
            label
        );


    const input =
        document.createElement(
            "input"
        );


    input.type =
        type;


    input.placeholder =
        placeholder;


    input.value =
        value ?? "";


    wrapper.appendChild(
        input
    );


    return {
        wrapper,
        input
    };
}


/*
 * 下拉框
 */
function createSelectField({
    label,
    value = "",
    options = []
}) {

    const wrapper =
        createFieldWrapper(
            label
        );


    const select =
        document.createElement(
            "select"
        );


    for (
        const optionData
        of options
    ) {

        const option =
            document.createElement(
                "option"
            );


        option.value =
            String(
                optionData.value
            );


        option.textContent =
            optionData.label;


        select.appendChild(
            option
        );
    }


    select.value =
        String(
            value ?? ""
        );


    wrapper.appendChild(
        select
    );


    return {
        wrapper,
        input: select
    };
}


/*
 * 多行文本框
 */
function createTextareaField({
    label,
    placeholder = "",
    value = ""
}) {

    const wrapper =
        createFieldWrapper(
            label
        );


    const textarea =
        document.createElement(
            "textarea"
        );


    textarea.placeholder =
        placeholder;


    textarea.value =
        value ?? "";


    wrapper.appendChild(
        textarea
    );


    return {
        wrapper,
        input: textarea
    };
}


/*
 * 字段包装
 */
function createFieldWrapper(
    labelText
) {

    const wrapper =
        document.createElement(
            "label"
        );


    wrapper.className =
        "data-source-form-field";


    const label =
        document.createElement(
            "span"
        );


    label.textContent =
        labelText;


    wrapper.appendChild(
        label
    );


    return wrapper;
}


/*
 * 显示 / 隐藏字段
 */
function setVisible(
    element,
    visible
) {

    element.style.display =
        visible
            ? ""
            : "none";
}


/*
 * 空字符串转 null
 */
function emptyToNull(
    value
) {

    const text =
        String(
            value ?? ""
        ).trim();


    return text
        ? text
        : null;
}


/*
 * 数字转换
 */
function numberOrNull(
    value
) {

    if (
        value === "" ||
        value === null ||
        value === undefined
    ) {

        return null;
    }


    const number =
        Number(value);


    return Number.isFinite(
        number
    )
        ? number
        : null;
}