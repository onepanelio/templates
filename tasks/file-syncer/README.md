# File-Syncer

Sidecar container for syncing files from multiple object storage providers. 

Currently supports:

- S3
- GCS
- Azure blob storage


## How to run

`file-syncer` is meant to run in Onepanel as a sidecar container. 

You can also run it via `docker` as follows:

```bash
# s3
docker run -it -v $(pwd)/files:/mnt -e AWS_ACCESS_KEY_ID=<value> -e AWS_SECRET_ACCESS_KEY=<value> file-syncer:latest \
    --provider s3 --path /mnt --storage-uri s3://mlpipeline.onepanel.io/rush  --direction up
```