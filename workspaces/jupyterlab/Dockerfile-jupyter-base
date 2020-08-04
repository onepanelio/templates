ARG BASE_CONTAINER=jupyter/scipy-notebook
FROM $BASE_CONTAINER

LABEL maintainer="OnepanelIO <aleksandr@onepanel.io>"

#Do not switch out root user, want to run as root.
USER root

RUN pip install --upgrade jupyterlab-git && \
    pip install --upgrade nbdime && \
    pip install --upgrade tensorboard && \
    jupyter labextension install @jupyterlab/github && \
    jupyter labextension install @jupyterlab/debugger && \
    jupyter lab build -y && \
    jupyter lab clean -y && \
    npm cache clean --force && \
    rm -rf "/home/${NB_USER}/.cache/yarn" && \
    rm -rf "/home/${NB_USER}/.node-gyp" && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"
