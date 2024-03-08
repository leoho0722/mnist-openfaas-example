# mnist-openfaas-example

## Environment Install

### Docker

[Docker Official Documentation](https://docs.docker.com/engine/install/ubuntu/)

#### Install Docker Engine on Ubuntu

* Step 1: Set up Docker's apt repository.

```shell
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```

* Step 2: Install the Docker packages.

```shell
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### OpenFaaS

See [openfaas-example README.md](https://github.com/leoho0722/openfaas-example/blob/main/README.md)

#### OpenFaaS Command Line Tool (faas-cli)

* macOS
  * ```brew install faas-cli```
* Ubuntu
  * Root user
    * ```curl -sSL https://cli.openfaas.com | sudo -E sh```
  * Non root user
    * ```curl -sSL https://cli.openfaas.com | sh```

#### Kubernetes

* Step 1: Create Kubernetes Namespace

    ```shell
    kubectl apply -f https://raw.githubusercontent.com/openfaas/faas-netes/master/namespaces.yml
    ```

* Step 2: Helm charts

    ```shell
    helm repo add openfaas https://openfaas.github.io/faas-netes/
    helm repo update
    helm upgrade openfaas --install openfaas/openfaas --namespace openfaas
    ```

* (**Optional**) Step 3: Expose OpenFaaS Gateway Service to LoadBalancer

    ```shell
    kubectl patch svc gateway-external -n openfaas -p '{"spec":{"type": "LoadBalancer"}}'
    ```

* Step 4: Get OpenFaaS admin Password

    ```shell
    PASSWORD=$(kubectl -n openfaas get secret basic-auth -o jsonpath="{.data.basic-auth-password}" | base64 --decode) && \
    echo "OpenFaaS admin password: $PASSWORD"
    ```

* Step 5: Login OpenFaaS WebUI via credential

    ```shell
    faas-cli login -u admin -p $PASSWORD
    ```

### MinIO Server

[MinIO Official Documentation](https://min.io/docs/minio/linux/index.html)

#### Install

* Ubuntu

  ```shell
  wget https://dl.min.io/server/minio/release/linux-amd64/archive/minio_20240305044844.0.0_amd64.deb -O minio.deb
  sudo dpkg -i minio.deb
  ```

#### Launch

```shell
mkdir ~/minio
minio server ~/minio --console-address :9001
```

#### Connect browser to MinIO Server

MinIO WebUI default account: minioadmin
MinIO WebUI default password: minioadmin

```text
http://<HOST_IP>:9001

# Example
# http://10.0.0.156:9001
```

### MinIO Client

[MinIO Official Documentation](https://min.io/docs/minio/linux/index.html)

#### Install

```shell
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
sudo mv mc /usr/local/bin/mc
```

#### Config

```shell
mc alias set <ALIAS_NAME> http://<HOST_IP>:9000 <ACCESS_KEY> <SECRET_KEY> 
mc admin info <ALIAS_NAME>

# Example
# mc alias set local http://10.0.0.156:9000 minioadmin minioadmin
# mc admin info local
```

##### Python Client API

[MinIO Python Client API Official Documentation](https://min.io/docs/minio/linux/developers/python/API.html)

```python
from minio import Minio

def connect_minio():
    """連接 MinIO Server"""

    MINIO_API_ENDPOINT = os.environ["minio_api_endpoint"]
    MINIO_ACCESS_KEY = os.environ["minio_access_key"]
    MINIO_SECRET_KEY = os.environ["minio_secret_key"]

    return Minio(
        MINIO_API_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False # 不使用 https 加密連線
    )
```

## Build, Push, Deploy, Remove OpenFaaS Functions

### One-key to build, push, deploy (**Recommand**)

```shell
make faas-up
```

### Manual

* Build

    ```shell
    make faas-build
    ```

* Push

    ```shell
    make faas-push
    ```

* Deploy

    ```shell
    make faas-deploy
    ```

* Remove

    ```shell
    make faas-remove
    ```

## References

1. <https://neptune.ai/blog/saving-trained-model-in-python>
