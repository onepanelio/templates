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
docker run -it -v $(pwd)/files:/mnt -e AWS_ACCESS_KEY_ID=<value> -e AWS_SECRET_ACCESS_KEY=<value> file-syncer:latest [upload|download] \
    --provider s3 --path /mnt --bucket <bucket> --prefix <prefix>

# gcs
docker run -it -v $(pwd)/files:/mnt -e GOOGLE_APPLICATION_CREDENTIALS=<key> file-syncer:latest [upload|download] \
    --provider gcs --path /mnt --bucket <bucket> --prefix <prefix>

# az
docker run -it -v $(pwd)/files:/mnt -e AZURE_STORAGE_ACCOUNT=<account> -e AZURE_STORAGE_KEY=<key> file-syncer:latest [upload|download] \
    --provider az --path /mnt --bucket <container> --prefix <prefix>
```
