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