# FileSyncer

Sidecar container for syncing files from the storage providers supported by Onepanel.

## How to run locally

`filesyncer` is meant to run in Onepanel as a sidecar container. For development, you can run it as follows.

### Server mode

In this mode, you can send HTTP requests to `filesyncer` to sync down from an object storage prefix to a local path or sync up from a local path to an object storage prefix.

To run `filesyncer` in server mode:

```bash
go run main.go server -server-prefix /sys/filesyncer
```

To test the endpoints:

```bash
# Sync down
curl localhost:8888/sys/filesyncer/api/sync -X POST --data '{"action": "download", "path":"/tmp", "prefix":"artifacts/my-namespace/"}'

# Sync up
curl localhost:8888/sys/filesyncer/api/sync -X POST --data '{"action": "upload", "path":"/tmp", "prefix":"artifacts/my-namespace/"}'
```

### Automatic syncing mode

```bash
FS_PATH=./files FS_PREFIX=data go run main.go upload
```

Note that this will work if you mock secret mounts by creating files for each secret key in `/etc/onepanel` folder locally. You can alternatively pass provider specific credentials as environment variables:

```bash
FS_PATH=./files FS_PREFIX=data FS_PROVIDER=s3 AWS_ACCESS_KEY_ID=<value> AWS_SECRET_ACCESS_KEY=<value> go run main.go upload
```

You can also indicate `provider`, `path` and `prefix` as flags:

```bash
AWS_ACCESS_KEY_ID=<value> AWS_SECRET_ACCESS_KEY=<value> go run main.go upload --path ./files --prefix data
```

You can also run via `docker` as follows:

```bash
docker run -it -v $(pwd)/files:/mnt -e AWS_ACCESS_KEY_ID=<value> -e AWS_SECRET_ACCESS_KEY=<value> filesyncer:0.17.0 [upload|download] \
    --path /mnt --bucket <bucket> --prefix <prefix>
```

Note that also indicate `FS_PROVIDER`, `FS_PATH` and `FS_PREFIX` as environment variables in the Docker commands, or you can mount the secret mocks like so:

```bash
docker run -v $(pwd)/files:/mnt -v $(pwd)/onepanel:/etc/onepanel -e FS_PATH=/mnt -e FS_PREFIX=data filesyncer:0.17.0 upload
```
