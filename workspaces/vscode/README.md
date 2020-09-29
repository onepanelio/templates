# VSCode Workspace

This Workspace uses the following images

* [codercom/code-server](https://hub.docker.com/r/codercom/code-server)

To Build
- Make sure your current directory is `vscode`
```shell script
docker build -t onepanel/vscode:1.0.0 .
```

To test locally:
```shell script
docker run -p 8080:8080 onepanel/vscode:1.0.0
```
To Release
```shell script
docker push onepanel/vscode:1.0.0
```