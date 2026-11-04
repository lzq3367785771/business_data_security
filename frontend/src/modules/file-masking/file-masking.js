import "./file-masking.css";

import {
    previewMaskingFile,
    executeFileMasking,
    getMaskingFilename,
    downloadMaskedFile
} from "./file-masking-api.js";


const MAX_FILE_SIZE =
    10 * 1024 * 1024;


const SENSITIVE_TYPES = [
    {
        value: "name",
        label: "姓名"
    },
    {
        value: "phone",
        label: "手机号"
    },
    {
        value: "id_card",
        label: "身份证号"
    },
    {
        value: "email",
        label: "邮箱"
    },
    {
        value: "address",
        label: "地址"
    },
    {
        value: "salary",
        label: "薪资"
    }
];


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
        size <
        1024 * 1024
    ) {

        return `${
            (
                size / 1024
            ).toFixed(2)
        } KB`;
    }


    return `${
        (
            size /
            1024 /
            1024
        ).toFixed(2)
    } MB`;
}


function validateFile(
    file
) {

    if (!file) {

        return "请选择 CSV 或 XLSX 文件";
    }


    if (
        file.size === 0
    ) {

        return "文件不能为空";
    }


    if (
        file.size >
        MAX_FILE_SIZE
    ) {

        return "文件大小不能超过 10 MB";
    }


    const filename =
        file.name.toLowerCase();


    if (
        !filename.endsWith(".csv") &&
        !filename.endsWith(".xlsx")
    ) {

        return "当前仅支持 CSV 和 XLSX 文件";
    }


    return null;
}


function createResultBox() {

    const box =
        document.createElement(
            "div"
        );


    box.className =
        "file-masking-result";


    box.hidden = true;


    return box;
}


function showResult(
    box,
    message,
    type = "success"
) {

    box.hidden = false;


    box.className =
        (
            "file-masking-result " +
            `file-masking-result-${type}`
        );


    box.textContent =
        message;
}


function createPage(
    content
) {

    content.replaceChildren();


    const page =
        document.createElement(
            "div"
        );


    page.className =
        "file-masking-page";


    const notice =
        document.createElement(
            "div"
        );


    notice.className =
        "file-masking-notice";


    const noticeTitle =
        document.createElement(
            "strong"
        );


    noticeTitle.textContent =
        "文件敏感数据脱敏";


    const noticeText =
        document.createElement(
            "span"
        );


    noticeText.textContent =
        (
            "上传 CSV 或 XLSX 文件后，平台会识别可能的敏感字段。" +
            "确认需要处理的字段后生成新的脱敏副本，不覆盖原始文件。"
        );


    notice.append(
        noticeTitle,
        noticeText
    );


    const uploadCard =
        document.createElement(
            "section"
        );


    uploadCard.className =
        "file-masking-card";


    const title =
        document.createElement(
            "h3"
        );


    title.textContent =
        "1. 上传并识别文件";


    const description =
        document.createElement(
            "p"
        );


    description.textContent =
        (
            "单个文件最大 10 MB。" +
            "预览结果只包含字段识别信息，不显示原始敏感数据。"
        );


    const fileInput =
        document.createElement(
            "input"
        );


    fileInput.type =
        "file";

    fileInput.accept =
        ".csv,.xlsx";

    fileInput.className =
        "file-masking-file-input";


    const fileInfo =
        document.createElement(
            "div"
        );


    fileInfo.className =
        "file-masking-file-info";

    fileInfo.hidden =
        true;


    const previewButton =
        document.createElement(
            "button"
        );


    previewButton.type =
        "button";

    previewButton.className =
        "file-masking-primary-button";

    previewButton.textContent =
        "识别敏感字段";

    previewButton.disabled =
        true;


    const resultBox =
        createResultBox();


    uploadCard.append(
        title,
        description,
        fileInput,
        fileInfo,
        previewButton,
        resultBox
    );


    const previewSection =
        document.createElement(
            "section"
        );


    previewSection.className =
        "file-masking-card";

    previewSection.hidden =
        true;


    const previewTitle =
        document.createElement(
            "h3"
        );


    previewTitle.textContent =
        "2. 确认需要脱敏的字段";


    const previewHint =
        document.createElement(
            "p"
        );


    previewHint.textContent =
        (
            "系统识别出的敏感字段会默认勾选。" +
            "你也可以人工调整字段类型或选择其他字段。"
        );


    const summary =
        document.createElement(
            "div"
        );


    summary.className =
        "file-masking-summary";


    const tables =
        document.createElement(
            "div"
        );


    tables.className =
        "file-masking-tables";


    const maskButton =
        document.createElement(
            "button"
        );


    maskButton.type =
        "button";

    maskButton.className =
        "file-masking-primary-button";

    maskButton.textContent =
        "执行脱敏并下载";

    maskButton.disabled =
        true;


    const maskResult =
        createResultBox();


    previewSection.append(
        previewTitle,
        previewHint,
        summary,
        tables,
        maskButton,
        maskResult
    );


    page.append(
        notice,
        uploadCard,
        previewSection
    );


    content.appendChild(
        page
    );


    return {
        fileInput,
        fileInfo,
        previewButton,
        resultBox,
        previewSection,
        summary,
        tables,
        maskButton,
        maskResult
    };
}


function createTypeSelect(
    value
) {

    const select =
        document.createElement(
            "select"
        );


    select.className =
        "file-masking-type-select";


    const empty =
        document.createElement(
            "option"
        );


    empty.value = "";

    empty.textContent =
        "请选择类型";


    select.appendChild(
        empty
    );


    for (
        const item
        of SENSITIVE_TYPES
    ) {

        const option =
            document.createElement(
                "option"
            );


        option.value =
            item.value;

        option.textContent =
            item.label;


        select.appendChild(
            option
        );
    }


    if (
        SENSITIVE_TYPES.some(
            item =>
                item.value === value
        )
    ) {

        select.value =
            value;
    }


    return select;
}


function confidenceText(
    value
) {

    if (
        value === null ||
        value === undefined
    ) {

        return "-";
    }


    return `${
        (
            Number(value) * 100
        ).toFixed(0)
    }%`;
}


function updateMaskButton(
    refs
) {

    const rows =
        refs.tables.querySelectorAll(
            ".file-masking-column-row"
        );


    let validCount = 0;


    for (
        const row
        of rows
    ) {

        const checkbox =
            row.querySelector(
                ".file-masking-checkbox"
            );


        const select =
            row.querySelector(
                ".file-masking-type-select"
            );


        if (
            checkbox.checked &&
            select.value
        ) {

            validCount += 1;
        }
    }


    refs.maskButton.disabled =
        validCount === 0;
}


function renderPreview(
    refs,
    data
) {

    refs.tables.replaceChildren();


    refs.previewSection.hidden =
        false;


    refs.summary.textContent =
        (
            `文件：${data.filename}　` +
            `类型：${data.file_type.toUpperCase()}　` +
            `大小：${formatFileSize(data.size_bytes)}　` +
            `识别敏感字段：${data.total_sensitive_columns}`
        );


    for (
        const sheet
        of data.sheets || []
    ) {

        const section =
            document.createElement(
                "div"
            );


        section.className =
            "file-masking-sheet";


        const heading =
            document.createElement(
                "div"
            );


        heading.className =
            "file-masking-sheet-title";


        heading.textContent =
            (
                `${sheet.sheet_name} ` +
                `（抽样 ${sheet.sampled_rows} 行）`
            );


        const wrapper =
            document.createElement(
                "div"
            );


        wrapper.className =
            "file-masking-table-wrapper";


        const table =
            document.createElement(
                "table"
            );


        table.className =
            "file-masking-table";


        const head =
            document.createElement(
                "thead"
            );


        head.innerHTML = `
            <tr>
                <th>选择</th>
                <th>字段</th>
                <th>敏感类型</th>
                <th>等级</th>
                <th>置信度</th>
                <th>识别方式</th>
                <th>识别说明</th>
            </tr>
        `;


        const body =
            document.createElement(
                "tbody"
            );


        for (
            const column
            of sheet.columns || []
        ) {

            const row =
                document.createElement(
                    "tr"
                );


            row.className =
                "file-masking-column-row";


            if (
                column.is_sensitive
            ) {

                row.classList.add(
                    "is-sensitive"
                );
            }


            row.dataset.sheetName =
                sheet.sheet_name;

            row.dataset.columnIndex =
                String(
                    column.column_index
                );


            const checkboxCell =
                document.createElement(
                    "td"
                );


            const checkbox =
                document.createElement(
                    "input"
                );


            checkbox.type =
                "checkbox";

            checkbox.className =
                "file-masking-checkbox";


            checkbox.checked =
                Boolean(
                    column.is_sensitive &&
                    column.sensitive_type
                );


            checkboxCell.appendChild(
                checkbox
            );


            const nameCell =
                document.createElement(
                    "td"
                );


            nameCell.textContent =
                column.column_name;


            const typeCell =
                document.createElement(
                    "td"
                );


            const typeSelect =
                createTypeSelect(
                    column.sensitive_type
                );


            typeCell.appendChild(
                typeSelect
            );


            const levelCell =
                document.createElement(
                    "td"
                );


            levelCell.textContent =
                column.sensitivity_level || "-";


            const confidenceCell =
                document.createElement(
                    "td"
                );


            confidenceCell.textContent =
                confidenceText(
                    column.confidence
                );


            const methodCell =
                document.createElement(
                    "td"
                );


            methodCell.textContent =
                column.detection_method || "-";


            const reasonCell =
                document.createElement(
                    "td"
                );


            reasonCell.textContent =
                column.detection_reason || "-";


            row.append(
                checkboxCell,
                nameCell,
                typeCell,
                levelCell,
                confidenceCell,
                methodCell,
                reasonCell
            );


            checkbox.addEventListener(
                "change",
                () => {

                    updateMaskButton(
                        refs
                    );
                }
            );


            typeSelect.addEventListener(
                "change",
                () => {

                    if (
                        typeSelect.value &&
                        !checkbox.checked
                    ) {

                        checkbox.checked =
                            true;
                    }


                    updateMaskButton(
                        refs
                    );
                }
            );


            body.appendChild(
                row
            );
        }


        table.append(
            head,
            body
        );


        wrapper.appendChild(
            table
        );


        section.append(
            heading,
            wrapper
        );


        refs.tables.appendChild(
            section
        );
    }


    updateMaskButton(
        refs
    );
}


function collectSelections(
    refs
) {

    const selections = [];


    const rows =
        refs.tables.querySelectorAll(
            ".file-masking-column-row"
        );


    for (
        const row
        of rows
    ) {

        const checkbox =
            row.querySelector(
                ".file-masking-checkbox"
            );


        const select =
            row.querySelector(
                ".file-masking-type-select"
            );


        if (!checkbox.checked) {

            continue;
        }


        if (!select.value) {

            throw new Error(
                "已勾选字段必须选择敏感类型"
            );
        }


        selections.push({
            sheet_name:
                row.dataset.sheetName,

            column_index:
                Number(
                    row.dataset.columnIndex
                ),

            sensitive_type:
                select.value
        });
    }


    if (
        selections.length === 0
    ) {

        throw new Error(
            "请至少选择一个需要脱敏的字段"
        );
    }


    return selections;
}


function buildFallbackFilename(
    filename
) {

    const index =
        filename.lastIndexOf(".");


    if (index <= 0) {

        return `${filename}_masked`;
    }


    return (
        filename.slice(
            0,
            index
        ) +
        "_masked" +
        filename.slice(
            index
        )
    );
}


export async function loadFileMasking(
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


    let selectedFile =
        null;


    statusMessage.textContent =
        "请选择需要脱敏的 CSV 或 XLSX 文件";


    refs.fileInput.addEventListener(
        "change",
        event => {

            selectedFile =
                event.target
                    .files?.[0]
                || null;


            refs.previewSection.hidden =
                true;

            refs.tables.replaceChildren();

            refs.resultBox.hidden =
                true;

            refs.maskResult.hidden =
                true;


            const error =
                validateFile(
                    selectedFile
                );


            if (error) {

                refs.fileInfo.hidden =
                    true;

                refs.previewButton.disabled =
                    true;

                statusMessage.textContent =
                    error;

                return;
            }


            refs.fileInfo.hidden =
                false;


            refs.fileInfo.textContent =
                (
                    `文件名称：${selectedFile.name}\n` +
                    `文件大小：${formatFileSize(selectedFile.size)}`
                );


            refs.previewButton.disabled =
                false;


            statusMessage.textContent =
                `已选择文件：${selectedFile.name}`;
        }
    );


    refs.previewButton.addEventListener(
        "click",

        async () => {

            const error =
                validateFile(
                    selectedFile
                );


            if (error) {

                showResult(
                    refs.resultBox,
                    error,
                    "error"
                );

                return;
            }


            refs.previewButton.disabled =
                true;

            refs.previewButton.textContent =
                "正在识别...";


            statusMessage.textContent =
                "正在识别文件中的敏感字段...";


            try {

                const data =
                    await previewMaskingFile(
                        selectedFile
                    );


                renderPreview(
                    refs,
                    data
                );


                showResult(
                    refs.resultBox,
                    (
                        "敏感字段识别完成。" +
                        `共发现 ${data.total_sensitive_columns} 个敏感字段。`
                    )
                );


                statusMessage.textContent =
                    "敏感字段识别完成，请确认需要脱敏的字段";

            } catch (error) {

                showResult(
                    refs.resultBox,
                    `识别失败：${error.message}`,
                    "error"
                );


                statusMessage.textContent =
                    `敏感字段识别失败：${error.message}`;

            } finally {

                refs.previewButton.disabled =
                    false;

                refs.previewButton.textContent =
                    "重新识别敏感字段";
            }
        }
    );


    refs.maskButton.addEventListener(
        "click",

        async () => {

            if (!selectedFile) {

                return;
            }


            let selections;


            try {

                selections =
                    collectSelections(
                        refs
                    );

            } catch (error) {

                showResult(
                    refs.maskResult,
                    error.message,
                    "error"
                );

                return;
            }


            refs.maskButton.disabled =
                true;

            refs.maskButton.textContent =
                "正在脱敏...";


            statusMessage.textContent =
                "正在生成脱敏文件...";


            try {

                const response =
                    await executeFileMasking(
                        selectedFile,
                        selections
                    );


                const fallbackFilename =
                    buildFallbackFilename(
                        selectedFile.name
                    );


                const filename =
                    getMaskingFilename(
                        response.headers,
                        fallbackFilename
                    );


                downloadMaskedFile(
                    response.blob,
                    filename
                );


                showResult(
                    refs.maskResult,
                    (
                        "文件脱敏成功，已生成并下载脱敏副本。\n" +
                        `处理字段数：${selections.length}`
                    )
                );


                statusMessage.textContent =
                    "文件脱敏成功";

            } catch (error) {

                showResult(
                    refs.maskResult,
                    `脱敏失败：${error.message}`,
                    "error"
                );


                statusMessage.textContent =
                    `文件脱敏失败：${error.message}`;

            } finally {

                refs.maskButton.textContent =
                    "执行脱敏并下载";


                updateMaskButton(
                    refs
                );
            }
        }
    );
}