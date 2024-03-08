import os
import requests

from minio import Minio
from minio.error import S3Error

TRAINED_MODEL_PKL_FILENAME = "trained_model.pkl"
TRAINING_RESULT_PKL_FILENAME = "training_result.pkl"
X_TEST4D_NORMALIZE_PKL_FILENAME = "X_Test4D_normalize.pkl"
Y_TEST_ONE_HOT_ENCODING_PKL_FILENAME = "y_TestOneHot.pkl"


def handle(req):
    """handle a request to the function

    Args:
        req (str): request body
    """

    minioClient = connect_minio()

    trained_model = get_file_from_bucket(client=minioClient,
                                         bucket_name="mnist-training-model",
                                         object_name=TRAINED_MODEL_PKL_FILENAME,
                                         file_path=f"/home/app/{TRAINED_MODEL_PKL_FILENAME}")
    # training_result = get_file_from_bucket(client=minioClient,
    #                                        bucket_name="mnist-training-model",
    #                                        object_name=TRAINING_RESULT_PKL_FILENAME,
    #                                        file_path=f"/home/app/{TRAINING_RESULT_PKL_FILENAME}")
    # 從 Minio 取得測試資料
    X_Test4D_normalize = get_file_from_bucket(client=minioClient,
                                              bucket_name="mnist-preprocess",
                                              object_name=X_TEST4D_NORMALIZE_PKL_FILENAME,
                                              file_path=f"/home/app/{X_TEST4D_NORMALIZE_PKL_FILENAME}")
    y_TestOneHot = get_file_from_bucket(client=minioClient,
                                        bucket_name="mnist-preprocess",
                                        object_name=Y_TEST_ONE_HOT_ENCODING_PKL_FILENAME,
                                        file_path=f"/home/app/{Y_TEST_ONE_HOT_ENCODING_PKL_FILENAME}")

    # 評估模型
    evaluate_model(trained_model, X_Test4D_normalize, y_TestOneHot)

    # 預測模型
    prediction_model(trained_model, X_Test4D_normalize)

    requeue = os.environ["requeue"]
    if requeue == 'true':
        next_stage = os.environ["next_stage"]
        trigger(next_stage)
        return response(200, f"mnist-model-evaluate completed, trigger stage {next_stage}...")

    return response(200, "mnist-model-evaluate completed...")


def evaluate_model(model, test_data, test_label):
    """評估模型

    Args:
        model (keras.models.Sequential): 訓練後的模型
        test_data: 標準化後的測試資料
        test_label: 標準化後的 onehot encoding 測試資料
    """

    scores = model.evaluate(test_data, test_label)
    print()
    print("\t[Info] Accuracy of testing data = {:2.1f}%".format(
        scores[1]*100.0))


def prediction_model(model, test_data):
    """預測模型

    Args:
        model (keras.models.Sequential): 訓練後的模型
        test_data: 標準化後的測試資料
    """

    print("\t[Info] Making prediction of X_Test4D_norm")
    # Making prediction and save result to prediction
    prediction = model.predict_classes(test_data)
    print()
    print("\t[Info] Show 10 prediction result (From 240):")
    print("%s\n" % (prediction[240:250]))


def connect_minio():
    """連接 Minio Server"""

    MINIO_API_ENDPOINT = os.environ["minio_api_endpoint"]
    MINIO_ACCESS_KEY = os.environ["minio_access_key"]
    MINIO_SECRET_KEY = os.environ["minio_secret_key"]

    return Minio(
        MINIO_API_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )


def get_bucket_names():
    """從環境變數中取得 Minio Bucket 名稱"""

    bucket_names = os.environ["bucket_names"]
    return bucket_names.split(",")


def create_buckets(client, bucket_names: list):
    """建立 Minio Bucket

    Args:
        client: Minio Client instance
        bucket_names (list[str]): 要建立的 Minio Bucket 名稱
    """

    for name in bucket_names:
        if client.bucket_exists(name):
            print(f"Bucket {name} already exists")
        else:
            client.make_bucket(name)
            print(f"Bucket {name} created")


def get_file_from_bucket(client, bucket_name, object_name, file_path):
    """取得 MinIO Bucket 內的資料

    Args:
        client: MinIO Client instance
        bucket_name (str): MinIO Bucket 名稱
        object_name (str): 要取得的 object 名稱
        file_path (str): 下載後的檔案路徑
    """

    client.fget_object(bucket_name, object_name, file_path)


def trigger(next_stage: str):
    """觸發下一個階段

    Args:
        next_stage (str): 下一個階段名稱
    """

    req_body = {
        "current_stage": "mnist-preprocess",
        "next_stage": next_stage
    }
    _ = requests.post(
        "http://10.0.0.156:31112/function/mnist-faas-trigger",
        json=req_body
    )


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
