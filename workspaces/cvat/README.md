# OpenCV CVAT Workspace

## Docker images

The docker images were created by cloning [opencv/cvat](https://github.com/opencv/cvat) and running this command:

```
docker-compose -f docker-compose.yml -f components/tf_annotation/docker-compose.tf_annotation.yml -f components/auto_segmentation/docker-compose.auto_segmentation.yml -f components/openvino/docker-compose.openvino.yml build
```

