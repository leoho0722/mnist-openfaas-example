import json
import requests
import threading


def handle(req):
    """handle a request to the function

    Args:
        req (str): request body
    """
    data = json.loads(req)
    next_stage = data["next_stage"]
    trigger_next_stage(next_stage)
    threading.Thread(target=trigger_next_stage(next_stage)).start()

    return response(200, f"next stage {next_stage} triggered...")


def trigger_next_stage(stage: str):
    """Trigger next stage

    Args:
        stage (str): next stage name
    """

    _ = requests.get(f"http://gateway.openfaas:8080/function/{stage}")
    print(f"next stage {stage} triggered...")


def response(statusCode: int, message: str):
    """Create an HTTP response.

    Args:
        statusCode (int): HTTP status code
        message (str): trigger message
    """

    return {
        "statusCode": statusCode,
        "message": message,
    }
