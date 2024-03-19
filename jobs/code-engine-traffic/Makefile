IMAGE_NAME := benchmark_app
CONTAINER_NAME := benchmark_app
# PORT :=  80
# LOCAL_PORT := 8080
REGISTRY := us.icr.io
NAMESPACE := rtiffany


# Default target for building the Docker image for the current ..PHONY: build
.PHONY: build
build:
	docker build -t $(REGISTRY)/$(NAMESPACE)/$(IMAGE_NAME) .

# Target for building the Docker image for ARM architecture
.PHONY: build-arm
build-arm:
	docker buildx build --platform linux/arm64 -t $(IMAGE_NAME):arm64 .

# Target for building the Docker image for x86 architecture
.PHONY: build-x86
build-x86:
	docker buildx build --platform linux/amd64 -t $(IMAGE_NAME):amd64 . 

.PHONY: run-arm
run-arm:
	docker run -d --name $(CONTAINER_NAME) $(IMAGE_NAME):arm64

.PHONY: build-and-push
build-and-push:
	docker buildx build --platform linux/amd64 -t $(REGISTRY)/$(NAMESPACE)/$(IMAGE_NAME):latest . --push



.PHONY: run-x86
run-x86:
	docker run --env-file=.env -it --name $(CONTAINER_NAME) $(IMAGE_NAME):amd64 http://example.com



.PHONY: clean
clean:
	docker rm -f $(IMAGE_NAME) || true
	docker rmi $(IMAGE_NAME) || true
