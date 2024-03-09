# Build, Push, Deploy Functions to OpenFaaS
ARCH ?= amd64
OPENFAAS_ENDPOINT = http:// 10.0.0.156:31112 # http://192.168.95.146:31112

.PHONY: faas-build
faas-build:
ifeq (($ARCH), arm64)
	faas-cli build -f mnist-pipeline.yml
else
	faas-cli build -f mnist-pipeline-amd64.yml
endif

.PHONY: faas-push
faas-push:
ifeq (($ARCH), arm64)
	faas-cli push -f mnist-pipeline.yml
else
	faas-cli push -f mnist-pipeline-amd64.yml
endif

.PHONY: faas-deploy
faas-deploy:
ifeq (($ARCH), arm64)
	faas-cli deploy -f mnist-pipeline.yml -g ${OPENFAAS_ENDPOINT}
else
	faas-cli deploy -f mnist-pipeline-amd64.yml -g ${OPENFAAS_ENDPOINT}
endif

.PHONY: faas-up
faas-up:
	make faas-build && make faas-push && make faas-deploy

.PHONY: faas-remove
faas-remove:
ifeq (($ARCH), arm64)
	faas-cli remove -f mnist-pipeline.yml -g ${OPENFAAS_ENDPOINT}
else
	faas-cli remove -f mnist-pipeline-amd64.yml -g ${OPENFAAS_ENDPOINT}
endif