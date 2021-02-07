ifndef version
	$(error version is undefined)
endif

docker-build:
	docker build -t onepanel/filesyncer:$(version) .

docker-push:
	docker push onepanel/filesyncer:$(version)

docker: docker-build docker-push