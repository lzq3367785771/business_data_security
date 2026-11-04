import {
    apiFormRequest,
    apiFileRequest
} from "../../services/api.js";


function buildPreviewFormData(
    file
) {

    const formData =
        new FormData();

    formData.append(
        "file",
        file
    );

    return formData;
}


/*
 * 文件敏感字段预览
 */
export async function previewMaskingFile(
    file
) {

    return apiFormRequest(
        "/file-masking/preview",
        buildPreviewFormData(
            file
        )
    );
}


/*
 * 执行文件脱敏
 */
export async function executeFileMasking(
    file,
    selections
) {

    const formData =
        new FormData();


    formData.append(
        "file",
        file
    );


    formData.append(
        "selections",
        JSON.stringify(
            selections
        )
    );


    return apiFileRequest(
        "/file-masking/mask",
        formData
    );
}


/*
 * 从 Content-Disposition
 * 读取下载文件名。
 */
export function getMaskingFilename(
    headers,
    fallbackFilename
) {

    const disposition =
        headers.get(
            "content-disposition"
        );


    if (!disposition) {

        return fallbackFilename;
    }


    const utf8Match =
        disposition.match(
            /filename\*=UTF-8''([^;]+)/i
        );


    if (utf8Match) {

        try {

            return decodeURIComponent(
                utf8Match[1]
            );

        } catch (error) {

            return utf8Match[1];
        }
    }


    const normalMatch =
        disposition.match(
            /filename="?([^";]+)"?/i
        );


    if (normalMatch) {

        return normalMatch[1];
    }


    return fallbackFilename;
}


/*
 * 下载 Blob
 */
export function downloadMaskedFile(
    blob,
    filename
) {

    const url =
        URL.createObjectURL(
            blob
        );


    const anchor =
        document.createElement(
            "a"
        );


    anchor.href =
        url;

    anchor.download =
        filename;


    document.body.appendChild(
        anchor
    );


    anchor.click();


    anchor.remove();


    URL.revokeObjectURL(
        url
    );
}