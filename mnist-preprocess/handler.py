import io
import numpy as np
import os
import requests
from keras.datasets import mnist
from keras.utils import np_utils
from minio import Minio
from minio.error import S3Error


def handle(req):
    """handle a request to the function

    Args:
        req (str): request body
    """

    minioClient = connect_minio()
    bucket_names = os.environ["bucket_names"]
    create_buckets(minioClient, bucket_names)

    X_Train4D_normalize, X_Test4D_normalize, y_TrainOneHot, y_TestOneHot = data_preprocess()

    # 上傳資料至 Minio Bucket
    # normalize
    upload_data_to_bucket(client=minioClient,
                          bucket_name=bucket_names[0],
                          object_name="X_Train4D_normalize",
                          upload_data=X_Train4D_normalize)
    upload_data_to_bucket(client=minioClient,
                          bucket_name=bucket_names[0],
                          object_name="X_Test4D_normalize",
                          upload_data=X_Test4D_normalize)
    # onehot encoding
    upload_data_to_bucket(client=minioClient,
                          bucket_name=bucket_names[1],
                          object_name="y_TrainOneHot",
                          upload_data=y_TrainOneHot)
    upload_data_to_bucket(client=minioClient,
                          bucket_name=bucket_names[1],
                          object_name="y_TestOneHot",
                          upload_data=y_TestOneHot)

    # 觸發下一個階段
    trigger(os.environ["next_stage"])

    return req


def data_preprocess():
    """資料預處理"""

    np.random.seed(10)

    # 讀取 mnist 資料集
    (X_train, y_train), (X_test, y_test) = mnist.load_data()

    # 資料轉換
    X_Train4D = X_train.reshape(X_train.shape[0], 28, 28, 1).astype('float32')
    X_Test4D = X_test.reshape(X_test.shape[0], 28, 28, 1).astype('float32')

    # 資料標準化
    X_Train4D_normalize, X_Test4D_normalize = data_normalize(
        X_Train4D, X_Test4D)

    # Label Onehot encoding
    y_TrainOneHot, y_TestOneHot = data_one_hot_encoding(y_train, y_test)

    return X_Train4D_normalize, X_Test4D_normalize, y_TrainOneHot, y_TestOneHot


def data_normalize(X_Train4D, X_Test4D):
    """資料標準化

    Args:
        X_Train4D (numpy.ndarray): 訓練資料
        X_Test4D (numpy.ndarray): 測試資料
    """

    X_Train4D_normalize = X_Train4D / 255
    X_Test4D_normalize = X_Test4D / 255

    return X_Train4D_normalize, X_Test4D_normalize


def data_one_hot_encoding(y_train, y_test):
    """Label Onehot encoding

    Args:
        y_train (numpy.ndarray): 訓練資料標籤
        y_test (numpy.ndarray): 測試資料標籤
    """

    y_TrainOneHot = np_utils.to_categorical(y_train)
    y_TestOneHot = np_utils.to_categorical(y_test)

    return y_TrainOneHot, y_TestOneHot


def connect_minio():
    """連接 Minio Server"""

    return Minio(
        "127.0.0.1:9001",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False
    )


def create_buckets(client, bucket_names: str):
    """建立 Minio Bucket

    Args:
        client: Minio Client instance
        bucket_names (str): 要建立的 Minio Bucket 名稱
    """

    names = bucket_names.split(",")

    for name in names:
        if not client.bucket_exists(name):
            client.make_bucket(name)
            print(f"Bucket {name} created")
        else:
            print(f"Bucket {name} already exists")


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
