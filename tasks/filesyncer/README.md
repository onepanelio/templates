# File-Syncer

Sidecar container for syncing files from multiple object storage providers. 

Currently supports:

- S3
- GCS
- Azure blob storage


## How to run locally

`file-syncer` is meant to run in Onepanel as a sidecar container. 

For development, you can run as follows:

```bash
FS_PATH=./files FS_PREFIX=data go run main.go upload
```

Note that this will work if you mock secret mounts by creating files for each secret key in `/etc/onepanel` folder locally. You can alternatively pass provider specific credentials as environment variables:

```bash
FS_PATH=./files FS_PREFIX=data FS_PROVIDER=s3 AWS_ACCESS_KEY_ID=<value> AWS_SECRET_ACCESS_KEY=<value> go run main.go upload
```

You can also indicate `provider`, `path` and `prefix` as flags:

```bash
AWS_ACCESS_KEY_ID=<value> AWS_SECRET_ACCESS_KEY=<value> go run main.go upload --provider s3 --path ./files --prefix data 
```

You can also run via `docker` as follows:

```bash
# s3
docker run -it -v $(pwd)/files:/mnt -e AWS_ACCESS_KEY_ID=<value> -e AWS_SECRET_ACCESS_KEY=<value> file-syncer:latest [upload|download] \
    --provider s3 --path /mnt --bucket <bucket> --prefix <prefix>

# gcs
docker run -it -v $(pwd)/files:/mnt -e GOOGLE_APPLICATION_CREDENTIALS=<key.json-path> file-syncer:latest [upload|download] \
    --provider gcs --path /mnt --bucket <bucket> --prefix <prefix>

# az
docker run -it -v $(pwd)/files:/mnt -e AZURE_STORAGE_ACCOUNT=<account> -e AZURE_STORAGE_KEY=<key> file-syncer:latest [upload|download] \
    --provider az --path /mnt --bucket <container> --prefix <prefix>
```

Note that also indicate `FS_PROVIDER`, `FS_PATH` and `FS_PREFIX` as environment variables in the Docker commands, or you can mount the secret mocks like so:

```bash
docker run -v $(pwd)/files:/mnt -v $(pwd)/onepanel:/etc/onepanel -e FS_PATH=/mnt -e FS_PREFIX=data filesyncer:gcs upload
```
