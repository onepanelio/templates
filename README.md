# Templates
Catalog of templates for Workflows, Workspaces, Tasks and Sidecars in Onepanel.

## Getting started
To get started, it's best to understand Onepanel's [Concepts](https://docs.onepanel.ai/docs/getting-started/concepts/namespaces) first.

See the following references for more information on how to build these templates:

- [Workspaces templates](https://docs.onepanel.ai/docs/reference/workspaces/templates)
- [Workflows templates](https://docs.onepanel.ai/docs/reference/workflows/templates)

## Catalog overview

### Workflow Templates
Workflow Templates consist of YAML definitions and Docker images that define a DAG in Onepanel. 

### Workspace Templates
Workspace Templates consist of YAML definitions and Docker images that define stateful instances like JupyterLab, CVAT and any other IDE.

### Sidecars
Sidecars are components that extend your Workspace or Workflow Tasks.

- [FileSyncer](sidecars/filesyncer) - Provides the APIs to sync files between Workspaces and default object storage.
- [NNI Web UI](sidecars/nni-web-ui) - Provides a proxy to NNI Web UI so that you can see the experiments in your hyperparameter tuning Workflows.

### Tasks
Tasks are the individual tasks in your Workflow (nodes in your DAG).
