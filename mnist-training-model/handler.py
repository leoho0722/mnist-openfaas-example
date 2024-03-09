import os
import pickle
import requests

from keras.layers import Conv2D, Dense, Dropout, Flatten, MaxPool2D
from keras.models import Sequential

from minio import Minio
from minio.error import S3Error


X_TRAIN4D_NORMALIZE_PKL_FILENAME = "X_Train4D_normalize.pkl"
Y_TRAIN_ONE_HOT_ENCODING_PKL_FILENAME = "y_Train_One_Hot_Encoding.pkl"
TRAINED_MODEL_KERAS_FILENAME = "trained_model.keras"
OPENFAAS_GATEWAY_ENDPOINT = os.environ["openfaas_gateway_endpoint"]


def handle(req):
    """handle a request to the function

    Args:
        req (str): request body
    """

    minioClient = connect_minio()
    bucket_names = get_bucket_names()
    create_buckets(minioClient, bucket_names)

    # 從 MinIO 取得上一個階段的資料
    get_file_from_bucket(client=minioClient,
                         bucket_name="mnist-normalize",
                         object_name=X_TRAIN4D_NORMALIZE_PKL_FILENAME,
                         file_path=f"/home/app/{X_TRAIN4D_NORMALIZE_PKL_FILENAME}")
    X_Train4D_normalize = convert_pkl_to_data(
        f"/home/app/{X_TRAIN4D_NORMALIZE_PKL_FILENAME}")
    get_file_from_bucket(client=minioClient,
                         bucket_name="mnist-onehot-encoding",
                         object_name=Y_TRAIN_ONE_HOT_ENCODING_PKL_FILENAME,
                         file_path=f"/home/app/{Y_TRAIN_ONE_HOT_ENCODING_PKL_FILENAME}")
    y_TrainOneHot = convert_pkl_to_data(
        f"/home/app/{Y_TRAIN_ONE_HOT_ENCODING_PKL_FILENAME}")

    # 建立模型
    model = model_build()

    # 訓練模型
    trained_model, _ = training_model(model=model, 
                                      normalize_data=X_Train4D_normalize,
                                      onehot_data=y_TrainOneHot)

    # 將訓練後的模型資料儲存到 MinIO Bucket
    save_trained_model(trained_model, TRAINED_MODEL_KERAS_FILENAME)
    upload_file_to_bucket(client=minioClient,
                          bucket_name=bucket_names[0],
                          object_name=TRAINED_MODEL_KERAS_FILENAME,
                          file_path=f"/home/app/{TRAINED_MODEL_KERAS_FILENAME}")

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


def save_trained_model(model, filename: str):
    """儲存訓練好的模型
    
    Args:
        model (keras.models.Sequential): keras.models.Sequential
        filename (str): 訓練好的模型檔名
    """

    model.save(filename)


def connect_minio():
    """連接 MinIO Server"""

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
    """從環境變數中取得 MinIO Bucket 名稱"""

    bucket_names = os.environ["bucket_names"]
    return bucket_names.split(",")


def create_buckets(client, bucket_names: list):
    """建立 MinIO Bucket

    Args:
        client: MinIO Client instance
        bucket_names (list): 要建立的 MinIO Bucket 名稱
    """

    for name in bucket_names:
        if client.bucket_exists(name):
            print(f"Bucket {name} already exists")
        else:
            client.make_bucket(name)
            print(f"Bucket {name} created")


def get_file_from_bucket(client, bucket_name: str, object_name: str, file_path: str):
    """取得 MinIO Bucket 內的資料

    Args:
        client: MinIO Client instance
        bucket_name (str): MinIO Bucket 名稱
        object_name (str): 要取得的 object 名稱
        file_path (str): 下載後的檔案路徑
    """

    client.fget_object(bucket_name, object_name, file_path)


def upload_file_to_bucket(client, bucket_name: str, object_name: str, file_path: str):
    """上傳資料到 MinIO Bucket 內

    Args:
        client: MinIO Client instance
        bucket_name (str): MinIO Bucket 名稱
        object_name (str): 要上傳到 MinIO Bucket 的 object 檔案名稱
        file_path (str): 要上傳到 MinIO Bucket 的檔案路徑
    """

    try:
        client.fput_object(bucket_name=bucket_name,
                           object_name=object_name,
                           file_path=file_path)
    except S3Error as err:
        print(
            f"upload file {file_path} to MinIO bucket {bucket_name} occurs error. Error: {err}"
        )


def convert_pkl_to_data(filename: str):
    """將 pkl 檔案轉換回原始資料
    
    Args:
        filename (str): pkl 檔案名稱
    """

    with open(filename, 'rb') as f:
        data = pickle.load(f)
    return data


def trigger(next_stage: str):
    """觸發下一個階段
    
    Args:
        next_stage (str): 下一個階段的名稱
    """

    req_body = {
        "next_stage": next_stage
    }
    _ = requests.post(
        f"http://{OPENFAAS_GATEWAY_ENDPOINT}/function/mnist-faas-trigger",
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
