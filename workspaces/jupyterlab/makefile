docker-build-base-notebook:
	cd base-notebook && make docker-build-base-notebook

docker-push-base-notebook:
	docker push onepanel/base-notebook:latest

docker-build-minimal-notebook:
	docker build -f Dockerfile-minimal-notebook -t minimal-notebook .
	docker tag minimal-notebook:latest onepanel/minimal-notebook:latest

docker-push-minimal-notebook:
	docker push onepanel/minimal-notebook:latest

docker-build-scipy-notebook:
	docker build -f Dockerfile-scipy-notebook -t scipy-notebook .
	docker tag scipy-notebook:latest onepanel/scipy-notebook:latest

docker-push-scipy-notebook:
	docker push onepanel/scipy-notebook:latest

docker-build-jupyter-base:
	docker build -f Dockerfile-jupyter-base -t jupyterlab-base .
	docker tag jupyterlab-base:latest onepanel/jupyterlab-base:latest

docker-push-jupyter-base:
	docker push onepanel/jupyterlab-base:latest

docker-build-tf-gpu:
	docker build -f Dockerfile-tf-gpu -t tensorflow-gpu .
	docker tag tensorflow-gpu:latest onepanel/tensorflow-gpu:latest

docker-push-tf-gpu:
	docker push onepanel/tensorflow-gpu:latest

docker-build-pytorch-gpu:
	docker build -f Dockerfile-pytorch-gpu -t pytorch-gpu .
	docker tag pytorch-gpu:latest onepanel/pytorch-gpu:latest

docker-push-pytorch-gpu:
	docker push onepanel/pytorch-gpu:latest

docker-build: docker-build-base-notebook docker-build-minimal-notebook docker-build-scipy-notebook \
	docker-build-jupyter-base docker-build-tf-gpu docker-build-pytorch-gpu

docker-push: docker-push-base-notebook docker-push-minimal-notebook docker-push-scipy-notebook \
	docker-push-jupyter-base docker-push-tf-gpu docker-push-pytorch-gpu

docker: docker-build docker-push