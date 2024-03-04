# Deploy MinIO Object Storage to Kubernetes
.PHONY: minio-deploy
minio-deploy:
	kubectl apply -f k8s/minio/

.PHONY: minio-port-forward
minio-port-forward:
	kubectl port-forward deployment/minio 9001 9090

# Delete MinIO Object Storage from Kubernetes
.PHONY: minio-delete
minio-delete:
	kubectl delete -f k8s/minio/

# Build, Push, Deploy Functions to OpenFaaS
.PHONY: faas-build
faas-build:
	faas-cli build -f mnist-pipeline.yml
.PHONY: faas-push
faas-push:
	faas-cli push -f mnist-pipeline.yml
.PHONY: faas-deploy
faas-deploy:
	faas-cli deploy -f mnist-pipeline.yml
.PHONY: faas-up
faas-up:
	make faas-build && make faas-push && make faas-deploy
.PHONY: faas-remove
faas-remove:
	faas-cli remove -f mnist-pipeline.yml