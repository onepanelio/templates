docker-build-base:
	docker build -f Dockerfile -t jupyterlab-base .
	docker tag jupyterlab-base:latest onepanel/jupyterlab-base:latest

docker-push-base:
	docker push onepanel/jupyterlab-base:latest

docker: docker-build-base docker-push-base