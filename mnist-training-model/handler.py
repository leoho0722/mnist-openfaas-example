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
    bucket_names = get_bucket_names()
    create_buckets(minioClient, bucket_names)

    # 從 Minio 取得上一個階段的資料
    X_Train4D_normalize = get_data_from_bucket(client=minioClient,
                                               bucket_name="mnist-normalize",
                                               object_name="X_Train4D_normalize",
                                               file_path="X_Train4D_normalize")
    y_TrainOneHot = get_data_from_bucket(client=minioClient,
                                         bucket_name="mnist-onehot-encoding",
                                         object_name="y_TrainOneHot",
                                         file_path="y_TrainOneHot")
    model = get_data_from_bucket(client=minioClient,
                                 bucket_name="mnist-model-build",
                                 object_name="build_model",
                                 file_path="build_model")
    # 訓練模型
    trained_model, training_result = training_model(model=model,
                                                    normalize_data=X_Train4D_normalize,
                                                    onehot_data=y_TrainOneHot)
    # 將訓練後的模型資料儲存到 Minio Bucket
    upload_data_to_bucket(client=minioClient,
                          bucket_name=bucket_names[0],
                          object_name="trained_model",
                          upload_data=trained_model)
    upload_data_to_bucket(client=minioClient,
                          bucket_name=bucket_names[0],
                          object_name="training_result",
                          upload_data=training_result)

    # 觸發下一個階段
    next_stage = os.environ["next_stage"]
    trigger(next_stage)

    return response(200, f"mnist-model-build completed, trigger stage {next_stage}...")


def training_model(model, normalize_data, onehot_data):
    """訓練模型

    Args:
        model (keras.models.Sequential): keras.models.Sequential
        normalize_data (numpy.ndarray): 標準化後的訓練資料
        onehot_data (numpy.ndarray): onehot encoding 後的訓練資料
    """

    # 定義訓練方式
    model.compile(loss='categorical_crossentropy',
                  optimizer='adam',
                  metrics=['accuracy'])

    # 開始訓練
    train_result = model.fit(x=normalize_data,
                             y=onehot_data,
                             validation_split=0.2,
                             epochs=10,
                             batch_size=300,
                             verbose=1)

    return model, train_result


def connect_minio():
    """連接 Minio Server"""

    return Minio(
        "127.0.0.1:9001",
        access_key="jvP0qXF2hzZ81TbxWjfK",
        secret_key="T2pgQ7IPinrV99tLmGrN7O5qhslc0Dkl7S6RW2oG",
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
        "current_stage": "mnist-training-model",
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
