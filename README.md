# Templates Catalog
Catalog of templates for Workflows, Workspaces, Tasks and Sidecars in Onepanel.

## Getting started
To get started, it's best to understand Onepanel's [Concepts](https://docs.onepanel.ai/docs/getting-started/concepts/namespaces) first.

See the following references for more information on how to build these templates:

- [Workspaces templates](https://docs.onepanel.ai/docs/reference/workspaces/templates)
- [Workflows templates](https://docs.onepanel.ai/docs/reference/workflows/templates)

## Catalog overview

### Workflow Templates
Workflow Templates consist of YAML definitions and Docker images that define a DAG in Onepanel.

- [Albumentations data pre-processing](https://github.com/onepanelio/templates/blob/master/workflows/albumentations-preprocessing) - This Workflow is included in [TFOD](https://github.com/onepanelio/templates/tree/release-v0.18.0/workflows/tf-object-detection-training) and [MaskRCNN](https://github.com/onepanelio/templates/tree/release-v0.18.0/workflows/maskrcnn-training) training Workflows and allows you to apply different augmentations to your data before training.
- [Auto CVAT](https://github.com/onepanelio/templates/blob/master/workflows/auto-cvat) - Allows you to automate your annotation workflow by creating CVAT instances and pre-populating them with data to be annotated.
- [Hyperparameter tuning](https://github.com/onepanelio/templates/blob/master/workflows/hyperparameter-tuning) - Hyperparameter tuning Workflow using [NNI](https://github.com/microsoft/nni). Included in Onepanel deployment.
- [MaskRCNN training](https://github.com/onepanelio/templates/blob/master/workflows/maskrcnn-training) - Workflow for semantic segmentation model training fully integrated with CVAT and included in Onepanel deployment.
- [PyTorch training](https://github.com/onepanelio/templates/blob/master/workflows/pytorch-mnist-training) - Simple MNIST training example using PyTorch.
- [TensorFlow training](https://github.com/onepanelio/templates/blob/master/workflows/tensorflow-mnist-training) - Simple MNIST training example using TensorFlow.
- [TensorFlow Object Detection training](https://github.com/onepanelio/templates/blob/master/workflows/tf-object-detection-training) - Workflow for object detection model training fully integrated with CVAT and included in Onepanel deployment. 

### Workspace Templates
Workspace Templates consist of YAML definitions and Docker images that define stateful instances like JupyterLab, CVAT and any other IDE.

- [CVAT](https://github.com/onepanelio/templates/blob/master/workspaces/cvat) - An interactive video and image annotation tool for computer vision.
- [JupyterLab](https://github.com/onepanelio/templates/blob/master/workspaces/jupyterlab) - An extensible environment for interactive and reproducible computing, based on Jupyter Notebook.
- [Eclipse Theia](https://github.com/onepanelio/templates/blob/master/workspaces/theia) - An extensible platform to develop multi-language cloud and desktop IDEs with state-of-the-art web technologies.
- [Ubuntu VNC](https://github.com/onepanelio/templates/blob/master/workspaces/vnc) (alpha) - A full Ubuntu instance accessible in your web browser.
- [Visual Studio Code](https://github.com/onepanelio/templates/blob/master/workspaces/vscode) - A lightweight but powerful source code editor which has support for just about everything. 

### Sidecars
Sidecars are components that extend your Workspace or Workflow Tasks.

- [FileSyncer](https://github.com/onepanelio/templates/blob/master/sidecars/filesyncer) - Provides the APIs to sync files between Workspaces and default object storage.
- [NNI Web UI](https://github.com/onepanelio/templates/blob/master/sidecars/nni-web-ui) - Provides a proxy to NNI Web UI so that you can see the experiments in your hyperparameter tuning Workflows.

### Tasks
Tasks are the individual tasks in your Workflow (nodes in your DAG).

- [Metrics writer](https://github.com/onepanelio/templates/blob/master/tasks/metrics-writer) - Task you can include to any Workflow Template to persist final metrics.
- [Slack notifications](https://github.com/onepanelio/templates/blob/master/tasks/slack-notify) - Task you can add to any Workflow or Workspace Template to send notifications to Slack.
