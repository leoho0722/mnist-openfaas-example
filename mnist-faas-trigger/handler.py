import json
import os
import requests
import threading

OPENFAAS_GATEWAY_ENDPOINT = os.environ["openfaas_gateway_endpoint"]

def handle(req):
    """handle a request to the function

    Args:
        req (str): request body
    """

    data = json.loads(req)
    next_stage = data["next_stage"]
    trigger_next_stage(next_stage)
    
    return response(200, f"next stage {next_stage} triggered...")


def trigger_next_stage(stage: str):
    """Trigger next stage

    Args:
        stage (str): next stage name
    """

    def trigger():
        _ = requests.get(
            f"http://{OPENFAAS_GATEWAY_ENDPOINT}/function/{stage}"
        )
        print(f"next stage {stage} triggered...")

    threading.Thread(target=trigger).start()


def response(statusCode: int, message: str):
    """Create an HTTP response.

    Args:
        statusCode (int): HTTP status code
        message (str): trigger message
    """

    return {
        "statusCode": statusCode,
        "message": message
    }
