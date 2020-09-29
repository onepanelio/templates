# Jupyter Notebook Deep Learning Stack and Visual Studio Code

This Workspace uses the following images

* [jupyter/tensorflow-notebook](https://hub.docker.com/r/jupyter/tensorflow-notebook) 
* [codercom/code-server](https://hub.docker.com/r/codercom/code-server)

To Build
- Make sure your current directory is `jupyterlab-and-vscode`
```shell script
docker build -t onepanel/vscode:1.0.0 -f Dockerfile-jupyterlab-and-vscode .
```

To test locally:
```shell script
docker run -p 8080:8080 onepanel/vscode:1.0.0
```
To Release
```shell script
docker push onepanel/vscode:1.0.0
```