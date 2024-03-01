import io
import os
import requests
from minio import Minio
from minio.error import S3Error


def handle(req):
    """handle a request to the function

    Args:
        req (str): request body
    """

    minioClient = connect_minio()

    # 從 Minio 取得上一個階段的資料
    trained_model = get_data_from_bucket(client=minioClient,
                                         bucket_name="mnist-training-model",
                                         object_name="trained_model",
                                         file_path="trained_model")
    # training_result = get_data_from_bucket(client=minioClient,
    #                                        bucket_name="mnist-training-model",
    #                                        object_name="trained_result",
    #                                        file_path="trained_result")
    # 從 Minio 取得測試資料
    test_data = get_data_from_bucket(client=minioClient,
                                     bucket_name="mnist-preprocess",
                                     object_name="X_Test4D_normalize",
                                     file_path="X_Test4D_normalize")
    test_label = get_data_from_bucket(client=minioClient,
                                      bucket_name="mnist-preprocess",
                                      object_name="y_TestOneHot",
                                      file_path="y_TestOneHot")

    # 評估模型
    evaluate_model(trained_model, test_data, test_label)
    # 預測模型
    prediction_model(trained_model, test_data)

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

    return Minio(
        "127.0.0.1:9001",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False
    )


def get_bucket_names():
    """從環境變數中取得 Minio Bucket 名稱"""

    bucket_names = os.environ["bucket_names"]
    return bucket_names.split(",")


def create_buckets(client, bucket_names: list[str]):
    """建立 Minio Bucket

    Args:
        client: Minio Client instance
        bucket_names (list[str]): 要建立的 Minio Bucket 名稱
    """

    for name in bucket_names:
        if not client.bucket_exists(name):
            client.make_bucket(name)
            print(f"Bucket {name} created")
        else:
            print(f"Bucket {name} already exists")


def get_data_from_bucket(client, bucket_name, object_name, file_path):
    """取得 Minio Bucket 內的資料

    Args:
        client: Minio Client instance
        bucket_name (str): Minio Bucket 名稱
        object_name (str): 要取得的 object 名稱
        file_path (str): 下載後的檔案路徑
    """

    try:
        data = client.get_object(bucket_name, object_name, file_path)
        return data
    except S3Error as err:
        print(
            f"get file from minio bucket {bucket_name} occurs error. Error: {err}")
    finally:
        data.close()
        data.release_conn()


def upload_data_to_bucket(client, bucket_name, object_name, upload_data):
    """上傳資料到 Minio Bucket 內

    Args:
        client: Minio Client instance
        bucket_name (str): Minio Bucket 名稱
        object_name (str): 要上傳到 Minio Bucket 的 object 名稱
        upload_data (object): 要上傳到 Minio Bucket 的資料
    """

    try:
        client.put_object(bucket_name=bucket_name,
                          object_name=object_name,
                          data=io.BytesIO(upload_data),
                          length=-1,
                          part_size=10*1024*1024)
    except S3Error as err:
        print(
            f"upload data {upload_data} to minio bucket {bucket_name} occurs error. Error: {err}"
        )


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
        "http://gateway.openfaas:8080/function/mnist-faas-trigger",
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
