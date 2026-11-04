import {
    apiFileRequest
} from "../../services/api.js";


function buildFileFormData(
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
 * 加密文件
 */
export async function encryptFile(
    file
) {

    return apiFileRequest(
        "/file-security/encrypt",
        buildFileFormData(
            file
        )
    );
}


/*
 * 解密文件
 */
export async function decryptFile(
    file
) {

    return apiFileRequest(
        "/file-security/decrypt",
        buildFileFormData(
            file
        )
    );
}


/*
 * 从 Content-Disposition 中解析下载文件名。
 */
export function getResponseFilename(
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


    /*
     * FastAPI 当前返回：
     *
     * attachment;
     * filename*=UTF-8''xxx.pdf.bdsec
     */
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
            /filename="?([^"]+)"?/i
        );


    if (normalMatch) {

        return normalMatch[1];
    }


    return fallbackFilename;
}


/*
 * 浏览器下载 Blob。
 */
export function downloadBlob(
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