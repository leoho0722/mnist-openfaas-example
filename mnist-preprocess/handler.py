import numpy as np
import os
import pickle
import requests

from keras import utils
from keras.datasets import mnist

from minio import Minio
from minio.error import S3Error


X_TRAIN4D_NORMALIZE_PKL_FILENAME = "X_Train4D_normalize.pkl"
X_TEST4D_NORMALIZE_PKL_FILENAME = "X_Test4D_normalize.pkl"
Y_TRAIN_ONE_HOT_ENCODING_PKL_FILENAME = "y_Train_One_Hot_Encoding.pkl"
Y_TEST_ONE_HOT_ENCODING_PKL_FILENAME = "y_TestOneHot.pkl"


def handle(req):
    """handle a request to the function

    Args:
        req (str): request body
    """

    minioClient = connect_minio()
    bucket_names = get_bucket_names()
    create_buckets(minioClient, bucket_names)

    X_Train4D_normalize, X_Test4D_normalize, y_TrainOneHot, y_TestOneHot = data_preprocess()
    write_file(f"{X_TRAIN4D_NORMALIZE_PKL_FILENAME}", X_Train4D_normalize)
    write_file(f"{X_TEST4D_NORMALIZE_PKL_FILENAME}", X_Test4D_normalize)
    write_file(f"{Y_TRAIN_ONE_HOT_ENCODING_PKL_FILENAME}", y_TrainOneHot)
    write_file(f"{Y_TEST_ONE_HOT_ENCODING_PKL_FILENAME}", y_TestOneHot)

    # 上傳檔案至 Minio Bucket
    # normalize
    upload_file_to_bucket(client=minioClient,
                          bucket_name=bucket_names[0],
                          object_name=X_TRAIN4D_NORMALIZE_PKL_FILENAME,
                          file_path=f"/home/app/{X_TRAIN4D_NORMALIZE_PKL_FILENAME}")
    upload_file_to_bucket(client=minioClient,
                          bucket_name=bucket_names[0],
                          object_name=X_TEST4D_NORMALIZE_PKL_FILENAME,
                          file_path=f"/home/app/{X_TEST4D_NORMALIZE_PKL_FILENAME}")
    # onehot encoding
    upload_file_to_bucket(client=minioClient,
                          bucket_name=bucket_names[1],
                          object_name=Y_TRAIN_ONE_HOT_ENCODING_PKL_FILENAME,
                          file_path=f"/home/app/{Y_TRAIN_ONE_HOT_ENCODING_PKL_FILENAME}")
    upload_file_to_bucket(client=minioClient,
                          bucket_name=bucket_names[1],
                          object_name=Y_TEST_ONE_HOT_ENCODING_PKL_FILENAME,
                          file_path=f"/home/app/{Y_TEST_ONE_HOT_ENCODING_PKL_FILENAME}")

    # 觸發下一個階段
    next_stage = os.environ["next_stage"]
    trigger(next_stage)

    return response(200, f"mnist-model-build completed, trigger stage {next_stage}...")


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

    y_TrainOneHot = utils.to_categorical(y_train)
    y_TestOneHot = utils.to_categorical(y_test)

    return y_TrainOneHot, y_TestOneHot


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
        bucket_names (list): 要建立的 Minio Bucket 名稱
    """

    print(f"bucket_names: {bucket_names}")
    for name in bucket_names:
        if client.bucket_exists(name):
            print(f"Bucket {name} already exists")
        else:
            client.make_bucket(name)
            print(f"Bucket {name} created")


def upload_file_to_bucket(client, bucket_name, object_name, file_path):
    """上傳資料到 Minio Bucket 內

    Args:
        client: Minio Client instance
        bucket_name (str): Minio Bucket 名稱
        object_name (str): 要上傳到 Minio Bucket 的 object 名稱
        filename (object): 要上傳到 Minio Bucket 的檔案名稱
    """

    try:
        client.fput_object(bucket_name=bucket_name,
                           object_name=object_name,
                           file_path=file_path)
    except S3Error as err:
        print(
            f"upload file {file_path} to minio bucket {bucket_name} occurs error. Error: {err}"
        )


def write_file(filename: str, data):
    with open(filename, 'wb') as f:
        pickle.dump(data, f)


def trigger(stage_name: str):
    """觸發下一個階段"""

    req_body = {
        "next_stage": stage_name
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
