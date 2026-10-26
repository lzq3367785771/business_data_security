export function formatLocalTime(
    value
) {

    if (!value) {
        return "-";
    }


    // 后端当前返回的是 UTC 时间，
    // 但 MySQL 序列化后没有携带 Z。
    const utcValue =
        value.endsWith("Z")
            ? value
            : `${value}Z`;


    const date =
        new Date(utcValue);


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {
        return value;
    }


    return date.toLocaleString(
        "zh-CN",
        {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            hour12: false,
        }
    );
}