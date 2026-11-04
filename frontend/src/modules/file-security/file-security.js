import "./file-security.css";

import {
    encryptFile,
    decryptFile,
    getResponseFilename,
    downloadBlob
} from "./file-security-api.js";


const MAX_FILE_SIZE =
    10 * 1024 * 1024;


/*
 * 格式化文件大小
 */
function formatFileSize(
    size
) {

    if (
        size === null ||
        size === undefined
    ) {
        return "-";
    }

    if (size < 1024) {
        return `${size} B`;
    }

    if (
        size < 1024 * 1024
    ) {
        return (
            `${(
                size / 1024
            ).toFixed(2)} KB`
        );
    }

    return (
        `${(
            size /
            1024 /
            1024
        ).toFixed(2)} MB`
    );
}


/*
 * 创建文件信息区域
 */
function createFileInfo() {

    const container =
        document.createElement(
            "div"
        );

    container.className =
        "file-security-file-info";

    container.hidden = true;


    const name =
        document.createElement(
            "div"
        );

    const type =
        document.createElement(
            "div"
        );

    const size =
        document.createElement(
            "div"
        );


    container.append(
        name,
        type,
        size
    );


    return {
        container,
        name,
        type,
        size
    };
}


/*
 * 更新文件信息
 */
function renderFileInfo(
    refs,
    file
) {

    if (!file) {

        refs.container.hidden =
            true;

        return;
    }


    refs.container.hidden =
        false;


    refs.name.textContent =
        `文件名称：${file.name}`;

    refs.type.textContent =
        `文件类型：${
            file.type ||
            "application/octet-stream"
        }`;

    refs.size.textContent =
        `文件大小：${
            formatFileSize(
                file.size
            )
        }`;
}


/*
 * 创建结果提示区域
 */
function createResultBox() {

    const box =
        document.createElement(
            "div"
        );

    box.className =
        "file-security-result";

    box.hidden = true;

    return box;
}


/*
 * 更新结果信息
 */
function showResult(
    box,
    message,
    type = "success"
) {

    box.hidden = false;

    box.className =
        (
            "file-security-result " +
            `file-security-result-${type}`
        );

    box.textContent =
        message;
}


/*
 * 创建操作卡片
 */
function createActionCard({
    title,
    description,
    accept,
    buttonText
}) {

    const card =
        document.createElement(
            "section"
        );

    card.className =
        "file-security-card";


    const header =
        document.createElement(
            "div"
        );

    header.className =
        "file-security-card-header";


    const titleElement =
        document.createElement(
            "h3"
        );

    titleElement.textContent =
        title;


    const descriptionElement =
        document.createElement(
            "p"
        );

    descriptionElement.textContent =
        description;


    header.append(
        titleElement,
        descriptionElement
    );


    const fileInput =
        document.createElement(
            "input"
        );

    fileInput.type =
        "file";

    fileInput.className =
        "file-security-file-input";

    if (accept) {

        fileInput.accept =
            accept;
    }


    const fileInfo =
        createFileInfo();


    const actionButton =
        document.createElement(
            "button"
        );

    actionButton.type =
        "button";

    actionButton.className =
        "file-security-primary-button";

    actionButton.textContent =
        buttonText;

    actionButton.disabled =
        true;


    const resultBox =
        createResultBox();


    card.append(
        header,
        fileInput,
        fileInfo.container,
        actionButton,
        resultBox
    );


    return {
        card,
        fileInput,
        fileInfo,
        actionButton,
        resultBox
    };
}


/*
 * 创建页面
 */
function createPage(
    content
) {

    content.replaceChildren();


    const page =
        document.createElement(
            "div"
        );

    page.className =
        "file-security-page";


    const notice =
        document.createElement(
            "div"
        );

    notice.className =
        "file-security-notice";


    const noticeTitle =
        document.createElement(
            "strong"
        );

    noticeTitle.textContent =
        "文件安全保护";


    const noticeText =
        document.createElement(
            "span"
        );

    noticeText.textContent =
        (
            " 当前 Mini V1 使用独立文件密钥进行加密保护，" +
            "单个文件最大支持 10 MB。"
        );


    notice.append(
        noticeTitle,
        noticeText
    );


    const grid =
        document.createElement(
            "div"
        );

    grid.className =
        "file-security-grid";


    const encryptCard =
        createActionCard({
            title:
                "文件加密",

            description:
                (
                    "上传业务文件后生成加密的 .bdsec 文件，" +
                    "原文件内容不会直接保存在加密包中。"
                ),

            accept:
                "",

            buttonText:
                "加密并下载"
        });


    const decryptCard =
        createActionCard({
            title:
                "文件解密",

            description:
                (
                    "上传平台生成的 .bdsec 文件，" +
                    "验证完整性后恢复原始文件。"
                ),

            accept:
                ".bdsec",

            buttonText:
                "解密并下载"
        });


    grid.append(
        encryptCard.card,
        decryptCard.card
    );


    page.append(
        notice,
        grid
    );


    content.appendChild(
        page
    );


    return {
        encryptCard,
        decryptCard
    };
}


/*
 * 校验文件
 */
function validateFile(
    file
) {

    if (!file) {

        return (
            "请选择文件"
        );
    }


    if (
        file.size === 0
    ) {

        return (
            "文件不能为空"
        );
    }


    if (
        file.size >
        MAX_FILE_SIZE
    ) {

        return (
            "文件大小不能超过 10 MB"
        );
    }


    return null;
}


/*
 * 加载文件安全页面
 */
export async function loadFileSecurity(
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


    statusMessage.textContent =
        (
            "文件安全模块已就绪，" +
            "请选择需要处理的文件"
        );


    /*
     * =========================
     * 加密文件选择
     * =========================
     */

    refs.encryptCard.fileInput
        .addEventListener(
            "change",
            event => {

                const file =
                    event.target
                        .files?.[0]
                    || null;


                renderFileInfo(
                    refs.encryptCard
                        .fileInfo,
                    file
                );


                const error =
                    validateFile(
                        file
                    );


                refs.encryptCard
                    .actionButton
                    .disabled =
                        Boolean(
                            error
                        );


                refs.encryptCard
                    .resultBox
                    .hidden =
                        true;


                statusMessage
                    .textContent =
                        error
                            ? error
                            : (
                                `已选择文件：${
                                    file.name
                                }`
                            );
            }
        );


    /*
     * =========================
     * 加密
     * =========================
     */

    refs.encryptCard
        .actionButton
        .addEventListener(
            "click",
            async () => {

                const file =
                    refs.encryptCard
                        .fileInput
                        .files?.[0];


                const error =
                    validateFile(
                        file
                    );


                if (error) {

                    showResult(
                        refs.encryptCard
                            .resultBox,
                        error,
                        "error"
                    );

                    return;
                }


                const button =
                    refs.encryptCard
                        .actionButton;


                button.disabled =
                    true;

                button.textContent =
                    "正在加密...";


                statusMessage
                    .textContent =
                        "正在加密文件...";


                try {

                    const response =
                        await encryptFile(
                            file
                        );


                    const filename =
                        getResponseFilename(
                            response.headers,
                            `${file.name}.bdsec`
                        );


                    downloadBlob(
                        response.blob,
                        filename
                    );


                    const sha256 =
                        response.headers.get(
                            "x-original-sha256"
                        );


                    showResult(
                        refs.encryptCard
                            .resultBox,

                        sha256
                            ? (
                                "文件加密成功并已下载。\n" +
                                `SHA-256：${sha256}`
                            )
                            : (
                                "文件加密成功并已下载。"
                            )
                    );


                    statusMessage
                        .textContent =
                            "文件加密成功";

                } catch (error) {

                    showResult(
                        refs.encryptCard
                            .resultBox,
                        `加密失败：${
                            error.message
                        }`,
                        "error"
                    );


                    statusMessage
                        .textContent =
                            (
                                "文件加密失败：" +
                                error.message
                            );

                } finally {

                    button.disabled =
                        false;

                    button.textContent =
                        "加密并下载";
                }
            }
        );


    /*
     * =========================
     * 解密文件选择
     * =========================
     */

    refs.decryptCard.fileInput
        .addEventListener(
            "change",
            event => {

                const file =
                    event.target
                        .files?.[0]
                    || null;


                renderFileInfo(
                    refs.decryptCard
                        .fileInfo,
                    file
                );


                let error =
                    validateFile(
                        file
                    );


                if (
                    !error &&
                    file &&
                    !file.name
                        .toLowerCase()
                        .endsWith(
                            ".bdsec"
                        )
                ) {

                    error =
                        (
                            "请选择平台生成的 " +
                            ".bdsec 加密文件"
                        );
                }


                refs.decryptCard
                    .actionButton
                    .disabled =
                        Boolean(
                            error
                        );


                refs.decryptCard
                    .resultBox
                    .hidden =
                        true;


                statusMessage
                    .textContent =
                        error
                            ? error
                            : (
                                `已选择加密文件：${
                                    file.name
                                }`
                            );
            }
        );


    /*
     * =========================
     * 解密
     * =========================
     */

    refs.decryptCard
        .actionButton
        .addEventListener(
            "click",
            async () => {

                const file =
                    refs.decryptCard
                        .fileInput
                        .files?.[0];


                const error =
                    validateFile(
                        file
                    );


                if (error) {

                    showResult(
                        refs.decryptCard
                            .resultBox,
                        error,
                        "error"
                    );

                    return;
                }


                const button =
                    refs.decryptCard
                        .actionButton;


                button.disabled =
                    true;

                button.textContent =
                    "正在解密...";


                statusMessage
                    .textContent =
                        "正在解密文件...";


                try {

                    const response =
                        await decryptFile(
                            file
                        );


                    const fallback =
                        file.name
                            .replace(
                                /\.bdsec$/i,
                                ""
                            );


                    const filename =
                        getResponseFilename(
                            response.headers,
                            fallback
                        );


                    downloadBlob(
                        response.blob,
                        filename
                    );


                    const sha256 =
                        response.headers.get(
                            "x-file-sha256"
                        );


                    showResult(
                        refs.decryptCard
                            .resultBox,

                        sha256
                            ? (
                                "文件解密成功并已下载。\n" +
                                `SHA-256：${sha256}`
                            )
                            : (
                                "文件解密成功并已下载。"
                            )
                    );


                    statusMessage
                        .textContent =
                            "文件解密成功";

                } catch (error) {

                    showResult(
                        refs.decryptCard
                            .resultBox,
                        `解密失败：${
                            error.message
                        }`,
                        "error"
                    );


                    statusMessage
                        .textContent =
                            (
                                "文件解密失败：" +
                                error.message
                            );

                } finally {

                    button.disabled =
                        false;

                    button.textContent =
                        "解密并下载";
                }
            }
        );
}