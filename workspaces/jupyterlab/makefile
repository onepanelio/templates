docker-build-base:
	docker build -f Dockerfile -t jupyterlab-base .
	docker tag jupyterlab-base:latest onepanel/jupyterlab-base:latest

docker-push-base:
	docker push onepanel/jupyterlab-base:latest

docker-build-tf-gpu:
	docker build -f Dockerfile-tf-gpu -t tensorflow-gpu .
	docker tag tensorflow-gpu:latest onepanel/tensorflow-gpu:latest

docker-push-tf-gpu:
	docker push onepanel/tensorflow-gpu:latest

docker: docker-build-base docker-push-base docker-build-tf-gpu docker-push-tf-gpu