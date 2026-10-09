from fastapi import Request


def success(
    request: Request,
    data=None,
    message: str = "success"
):
    return {
        "code": 0,
        "message": message,
        "data": data,
        "request_id": request.state.request_id
    }