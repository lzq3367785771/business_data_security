import {
    apiRequest
} from "../../services/api.js";


/*
 * 查询敏感字段画像
 */
export async function fetchSensitiveFields(
    filters = {}
) {

    const params =
        new URLSearchParams();


    params.set(
        "is_sensitive",
        "true"
    );


    if (filters.reviewStatus) {

        params.set(
            "review_status",
            filters.reviewStatus
        );
    }


    if (filters.sensitivityLevel) {

        params.set(
            "sensitivity_level",
            filters.sensitivityLevel
        );
    }


    const queryString =
        params.toString();


    return apiRequest(
        `/sensitive-fields?${queryString}`
    );
}


/*
 * 人工复核敏感字段
 */
export async function reviewSensitiveField(
    profileId,
    reviewStatus
) {

    const confirmed =
        reviewStatus === "confirmed";


    return apiRequest(
        `/sensitive-fields/${profileId}/review`,
        {
            method: "PATCH",

            body: {
                review_status:
                    reviewStatus,

                note:
                    confirmed
                        ? "管理员通过前端确认识别结果"
                        : "管理员通过前端驳回识别结果"
            }
        }
    );
}