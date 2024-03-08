# Deploy MinIO Object Storage to Kubernetes
.PHONY: minio-deploy
minio-deploy:
	kubectl apply -f k8s/minio/namespace.yaml && \
		kubectl apply -f k8s/minio/deployment.yaml && \
		kubectl apply -f k8s/minio/svc.yaml

.PHONY: minio-port-forward
minio-port-forward:
	kubectl port-forward -n minio deployment/minio 9001 9090

# Delete MinIO Object Storage from Kubernetes
.PHONY: minio-delete
minio-delete:
	kubectl delete -f k8s/minio/

# ===== OpenFaaS =====

# Deploy OpenFaaS to Kubernetes
.PHONY: faas-k8s-deploy
faas-k8s-deploy:
	kubectl apply -f k8s/openfaas/

# Delete OpenFaaS from Kubernetes
.PHONY: faas-k8s-delete
faas-k8s-delete:
	kubectl delete -f k8s/openfaas/

# Build, Push, Deploy Functions to OpenFaaS
OPENFAAS_ENDPOINT = http://10.0.0.156:31112

.PHONY: faas-build
faas-build:
	faas-cli build -f mnist-pipeline.yml

.PHONY: faas-push
faas-push:
	faas-cli push -f mnist-pipeline.yml

.PHONY: faas-deploy
faas-deploy:
	faas-cli deploy -f mnist-pipeline.yml -g ${OPENFAAS_ENDPOINT}

.PHONY: faas-up
faas-up:
	make faas-build && make faas-push && make faas-deploy

.PHONY: faas-remove
faas-remove:
	faas-cli remove -f mnist-pipeline.yml -g ${OPENFAAS_ENDPOINT}