.PHONY: init

init:
ifndef version
	$(error version is undefined)
endif

docker-build-base-notebook:
	docker build -f Dockerfile-base-notebook -t base-notebook .
	docker tag base-notebook:latest onepanel/base-notebook:$(version)