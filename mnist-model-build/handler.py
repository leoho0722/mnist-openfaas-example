import io
import os
import requests
from keras.layers import Dense, Dropout, Flatten, Conv2D, MaxPool2D
from keras.models import Sequential
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

    build_model = model_build()

    # 上傳資料至 Minio Bucket
    upload_data_to_bucket(client=minioClient,
                          bucket_name=bucket_names[0],
                          object_name="build_model",
                          upload_data=build_model)

    # 觸發下一個階段
    next_stage = os.environ["next_stage"]
    trigger(next_stage)

    return response(200, f"mnist-model-build completed, trigger stage {next_stage}...")


def model_build():
    """建立模型"""

    model = Sequential()
    create_cn_layer_and_pool_layer(model)
    create_flatten_layer_and_hidden_layer(model)
    model_summary(model)

    return model


def create_cn_layer_and_pool_layer(model):
    """建立卷積層與池化層

    Args:
        model (keras.models.Sequential): keras.models.Sequential
    """

    # Create CN layer 1
    model.add(Conv2D(filters=16,
                     kernel_size=(5, 5),
                     padding='same',
                     input_shape=(28, 28, 1),
                     activation='relu',
                     name='conv2d_1'))
    # Create Max-Pool 1
    model.add(MaxPool2D(pool_size=(2, 2), name='max_pooling2d_1'))

    # Create CN layer 2
    model.add(Conv2D(filters=36,
                     kernel_size=(5, 5),
                     padding='same',
                     input_shape=(28, 28, 1),
                     activation='relu',
                     name='conv2d_2'))

    # Create Max-Pool 2
    model.add(MaxPool2D(pool_size=(2, 2), name='max_pooling2d_2'))

    # Add Dropout layer
    model.add(Dropout(0.25, name='dropout_1'))


def create_flatten_layer_and_hidden_layer(model):
    """建立平坦層與隱藏層

    Args:
        model (keras.models.Sequential): keras.models.Sequential
    """

    # Create Flatten layer
    model.add(Flatten(name='flatten_1'))

    # Create Hidden layer
    model.add(Dense(128, activation='relu', name='dense_1'))
    model.add(Dropout(0.5, name='dropout_2'))

    # Create Output layer
    model.add(Dense(10, activation='softmax', name='dense_2'))


def model_summary(model):
    """顯示模型摘要

    Args:
        model (keras.models.Sequential): keras.models.Sequential
    """

    model.summary()
    print("Model is built successfully!")


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
        "current_stage": "mnist-model-build",
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
