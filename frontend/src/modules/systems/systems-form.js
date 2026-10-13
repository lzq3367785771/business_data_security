/*
 * 创建业务系统表单弹窗
 *
 * options:
 * {
 *     title,
 *     initialData,
 *     onSubmit,
 *     onClose
 * }
 */
export function createSystemFormModal({
    title = "新增业务系统",
    initialData = null,
    onSubmit,
    onClose
}) {

    // =========================
    // 遮罩层
    // =========================

    const overlay =
        document.createElement("div");

    overlay.className =
        "system-modal-overlay";


    // =========================
    // 弹窗主体
    // =========================

    const modal =
        document.createElement("div");

    modal.className =
        "system-modal";


    // =========================
    // 标题栏
    // =========================

    const header =
        document.createElement("div");

    header.className =
        "system-modal-header";


    const titleElement =
        document.createElement("h3");

    titleElement.textContent =
        title;


    const closeButton =
        document.createElement("button");

    closeButton.type =
        "button";

    closeButton.className =
        "system-modal-close";

    closeButton.textContent =
        "×";


    header.append(
        titleElement,
        closeButton
    );


    // =========================
    // 表单
    // =========================

    const form =
        document.createElement("form");

    form.className =
        "system-form";


    const codeField =
        createInputField({
            label: "系统编码",
            name: "system_code",
            required: true,
            placeholder: "例如 CRM、HR、FINANCE",
            value:
                initialData?.system_code || "",
            readOnly:
                Boolean(initialData)
        });


    const nameField =
        createInputField({
            label: "系统名称",
            name: "system_name",
            required: true,
            placeholder: "例如 客户关系管理系统",
            value:
                initialData?.system_name || ""
        });


    const typeField =
        createSelectField({
            label: "系统类型",
            name: "system_type",
            required: true,
            value:
                initialData?.system_type || "web",

            options: [
                {
                    value: "web",
                    label: "Web 系统"
                },
                {
                    value: "app",
                    label: "应用系统"
                },
                {
                    value: "api",
                    label: "API 系统"
                },
                {
                    value: "mixed",
                    label: "混合系统"
                }
            ]
        });


    const environmentField =
        createSelectField({
            label: "运行环境",
            name: "environment",
            required: true,
            value:
                initialData?.environment || "test",

            options: [
                {
                    value: "dev",
                    label: "开发"
                },
                {
                    value: "test",
                    label: "测试"
                },
                {
                    value: "prod",
                    label: "生产"
                }
            ]
        });


    const departmentField =
        createInputField({
            label: "责任部门",
            name: "owner_department",
            placeholder: "可选",
            value:
                initialData?.owner_department || ""
        });


    const urlField =
        createInputField({
            label: "系统访问地址",
            name: "base_url",
            placeholder:
                "例如 https://crm.example.com",
            value:
                initialData?.base_url || ""
        });


    const descriptionField =
        createTextareaField({
            label: "系统描述",
            name: "description",
            placeholder: "可选",
            value:
                initialData?.description || ""
        });


    const grid =
        document.createElement("div");

    grid.className =
        "system-form-grid";


    grid.append(
        codeField.wrapper,
        nameField.wrapper,
        typeField.wrapper,
        environmentField.wrapper,
        departmentField.wrapper,
        urlField.wrapper
    );


    form.append(
        grid,
        descriptionField.wrapper
    );


    // =========================
    // 错误提示
    // =========================

    const errorMessage =
        document.createElement("div");

    errorMessage.className =
        "system-form-error";


    form.appendChild(
        errorMessage
    );


    // =========================
    // 底部按钮
    // =========================

    const footer =
        document.createElement("div");

    footer.className =
        "system-modal-footer";


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
        initialData
            ? "保存修改"
            : "创建系统";


    footer.append(
        cancelButton,
        submitButton
    );


/*
 * 底部按钮必须放在 form 内部，
 * 否则 submitButton 无法触发表单 submit 事件。
 */
form.appendChild(
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
    // 关闭弹窗
    // =========================

    function closeModal() {

        overlay.remove();

        if (
            typeof onClose ===
            "function"
        ) {

            onClose();
        }
    }


    closeButton.addEventListener(
        "click",
        closeModal
    );


    cancelButton.addEventListener(
        "click",
        closeModal
    );


    overlay.addEventListener(
        "click",
        event => {

            if (
                event.target ===
                overlay
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


            const payload = {
                system_code:
                    codeField.input.value
                        .trim()
                        .toUpperCase(),

                system_name:
                    nameField.input.value
                        .trim(),

                system_type:
                    typeField.select.value,

                environment:
                    environmentField.select.value,

                owner_department:
                    emptyToNull(
                        departmentField.input.value
                    ),

                base_url:
                    emptyToNull(
                        urlField.input.value
                    ),

                description:
                    emptyToNull(
                        descriptionField.textarea.value
                    )
            };


            if (
                !payload.system_code ||
                !payload.system_name
            ) {

                errorMessage.textContent =
                    "请填写系统编码和系统名称";

                return;
            }


            submitButton.disabled =
                true;


            try {

                await onSubmit(
                    payload
                );

                closeModal();

            } catch (error) {

                errorMessage.textContent =
                    error.message;

            } finally {

                submitButton.disabled =
                    false;
            }
        }
    );
}


/*
 * 创建普通输入框
 */
function createInputField({
    label,
    name,
    required = false,
    placeholder = "",
    value = "",
    readOnly = false
}) {

    const wrapper =
        createFieldWrapper(
            label
        );


    const input =
        document.createElement("input");

    input.type =
        "text";

    input.name =
        name;

    input.required =
        required;

    input.placeholder =
        placeholder;

    input.value =
        value;

    input.readOnly =
        readOnly;


    if (readOnly) {

        input.classList.add(
            "system-form-readonly"
        );

        input.title =
            "系统编码创建后不可修改";
    }



    wrapper.appendChild(
        input
    );


    return {
        wrapper,
        input
    };
}


/*
 * 创建下拉框
 */
function createSelectField({
    label,
    name,
    required = false,
    value,
    options
}) {

    const wrapper =
        createFieldWrapper(
            label
        );


    const select =
        document.createElement("select");

    select.name =
        name;

    select.required =
        required;


    options.forEach(option => {

        const element =
            document.createElement("option");

        element.value =
            option.value;

        element.textContent =
            option.label;

        select.appendChild(
            element
        );
    });


    select.value =
        value;


    wrapper.appendChild(
        select
    );


    return {
        wrapper,
        select
    };
}


/*
 * 创建多行文本框
 */
function createTextareaField({
    label,
    name,
    placeholder = "",
    value = ""
}) {

    const wrapper =
        createFieldWrapper(
            label
        );


    const textarea =
        document.createElement("textarea");

    textarea.name =
        name;

    textarea.placeholder =
        placeholder;

    textarea.rows =
        4;

    textarea.value =
        value;


    wrapper.appendChild(
        textarea
    );


    return {
        wrapper,
        textarea
    };
}


/*
 * 创建字段外层
 */
function createFieldWrapper(
    labelText
) {

    const wrapper =
        document.createElement("label");

    wrapper.className =
        "system-form-field";


    const label =
        document.createElement("span");

    label.textContent =
        labelText;


    wrapper.appendChild(
        label
    );


    return wrapper;
}


/*
 * 空字符串转换为 null
 */
function emptyToNull(
    value
) {

    const normalized =
        value.trim();

    return normalized
        ? normalized
        : null;
}