.PHONY: init

init:
ifndef version
	$(error version is undefined)
endif

docker-build-base-notebook:
	cd base-notebook && make docker-build-base-notebook

docker-push-base-notebook:
	docker push onepanel/base-notebook:$(version)

docker-build-minimal-notebook:
	docker build --build-arg CONTAINER_TAG=$(version) -f Dockerfile-minimal-notebook -t minimal-notebook .
	docker tag minimal-notebook:latest onepanel/minimal-notebook:$(version)

docker-push-minimal-notebook:
	docker push onepanel/minimal-notebook:$(version)

docker-build-scipy-notebook:
	docker build --build-arg CONTAINER_TAG=$(version) -f Dockerfile-scipy-notebook -t scipy-notebook .
	docker tag scipy-notebook:latest onepanel/scipy-notebook:$(version)

docker-push-scipy-notebook:
	docker push onepanel/scipy-notebook:$(version)

docker-build-jupyter-base:
	docker build --build-arg CONTAINER_TAG=$(version) -f Dockerfile-jupyter-base -t jupyterlab-base .
	docker tag jupyterlab-base:latest onepanel/jupyterlab-base:$(version)

docker-push-jupyter-base:
	docker push onepanel/jupyterlab-base:$(version)

docker-build-opencv-base:
	docker build --build-arg CONTAINER_TAG=$(version) -f Dockerfile-opencv -t opencv-base .
	docker tag opencv-base:latest onepanel/opencv-base:$(version)

docker-push-opencv-base:
	docker push onepanel/opencv-base:$(version)

docker-build-tf-gpu:
	docker build --build-arg CONTAINER_TAG=$(version) -f Dockerfile-tf-gpu -t tensorflow-gpu .
	docker tag tensorflow-gpu:latest onepanel/tensorflow-gpu:$(version)

docker-push-tf-gpu:
	docker push onepanel/tensorflow-gpu:$(version)

docker-build-pytorch-gpu:
	docker build --build-arg CONTAINER_TAG=$(version) -f Dockerfile-pytorch-gpu -t pytorch-gpu .
	docker tag pytorch-gpu:latest onepanel/pytorch-gpu:$(version)

docker-push-pytorch-gpu:
	docker push onepanel/pytorch-gpu:$(version)

docker-build: docker-build-base-notebook docker-build-minimal-notebook docker-build-scipy-notebook \
	docker-build-jupyter-base docker-build-opencv-base docker-build-tf-gpu docker-build-pytorch-gpu

docker-push: docker-push-base-notebook docker-push-minimal-notebook docker-push-scipy-notebook \
	docker-push-jupyter-base docker-push-opencv-base docker-push-tf-gpu docker-push-pytorch-gpu

docker: docker-build docker-push