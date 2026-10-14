from app.db.models import Customer


def mask_phone(value: str) -> str:
    if len(value) < 7:
        return "****"

    return value[:3] + "****" + value[-4:]


def mask_id_card(value: str) -> str:
    if len(value) < 8:
        return "****"

    hidden = "*" * (len(value) - 7)

    return value[:3] + hidden + value[-4:]


def present_customer(
    customer: Customer,
    mask_fields: tuple[str, ...]
) -> dict:

    data = {
        "id": customer.id,
        "name": customer.name,
        "phone": customer.phone,
        "id_card": customer.id_card
    }

    if "phone" in mask_fields:
        data["phone"] = mask_phone(data["phone"])

    if "id_card" in mask_fields:
        data["id_card"] = mask_id_card(
            data["id_card"]
        )

    return data



def mask_name(value) -> str:

    text = str(value)

    if not text:
        return ""

    if len(text) == 1:
        return "*"

    return (
        text[0]
        + "*" * (len(text) - 1)
    )


def mask_email(value) -> str:

    text = str(value)

    if "@" not in text:
        return "****"

    local, domain = text.split(
        "@",
        1,
    )

    if not local:
        return f"***@{domain}"

    return (
        local[0]
        + "***@"
        + domain
    )


def mask_address(value) -> str:

    text = str(value)

    if len(text) <= 3:
        return "***"

    return (
        text[:3]
        + "******"
    )


def mask_salary(value) -> str:

    return "******"


def mask_generic(value) -> str:

    return "******"


def mask_value(
    value,
    sensitive_type: str | None,
):
    """
    根据敏感类型执行动态脱敏。
    """

    if value is None:
        return None

    text = str(value)

    handlers = {
        "name": mask_name,
        "phone": mask_phone,
        "id_card": mask_id_card,
        "email": mask_email,
        "address": mask_address,
        "salary": mask_salary,
    }

    handler = handlers.get(
        sensitive_type,
        mask_generic,
    )

    return handler(text)


def mask_rows(
    rows: list[dict],
    field_types: dict[str, str],
) -> list[dict]:
    """
    对业务数据结果进行字段级动态脱敏。

    field_types 示例：

    {
        "name": "name",
        "phone": "phone",
        "salary": "salary"
    }
    """

    masked_rows = []

    for row in rows:

        new_row = dict(row)

        for (
            column_name,
            sensitive_type,
        ) in field_types.items():

            if column_name not in new_row:
                continue

            new_row[column_name] = (
                mask_value(
                    new_row[column_name],
                    sensitive_type,
                )
            )

        masked_rows.append(
            new_row
        )

    return masked_rows