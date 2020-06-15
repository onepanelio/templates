import boto3
import os
import logging
import time


LAST_LEN_KEYS = 0
S3 = boto3.client('s3')

formatter = '%(asctime)s %(levelname)s %(message)s'
logging.basicConfig(format=formatter, level=logging.INFO)
wlogger = logging.getLogger("s3-watcher")
# log_file = logging.FileHandler('/var/tmp/s3watcher.log')
# log_file.setFormatter(formatter)
# wlogger.addHandler(log_file)


def get_list_keys(bucket, dir):
    paginator = S3.get_paginator('list_objects_v2')
    keys = []
    for page in paginator.paginate(Bucket=bucket, Prefix=dir):
        try:
            contents = page['Contents']
        except KeyError as e:
            wlogger.warning("An exception occurred.")
            break

        for cont in contents:
            keys.append(cont['Key'])
    return keys


def new_files(bucket, dir, local_dir):
    global LAST_LEN_KEYS
    keys = get_list_keys(bucket, dir)
    wlogger.info(f"Number of keys found: {len(keys)}")
    if len(keys) > LAST_LEN_KEYS:
        LAST_LEN_KEYS = len(keys)
        return True
    return False

def run_sync():
    wlogger.info(f"Running run_sync function, current length {LAST_LEN_KEYS}")
    # if there are new files on s3 then run sync command
    bucket = os.getenv('SYNCER_S3_BUCKET_NAME','cnas-re.uog.onepanel.io')
    dir = os.getenv('S3_SYNC_PATH','')
    local_dir = os.getenv('LOCAL_SYNC_PATH','/mnt/share/')
    direction = os.getenv('SYNC_DIRECTION', 'up') # up - upload to s3, down - download from s3, or both
    if new_files(bucket, dir, local_dir):
        #run cli commands
        if direction == "down":
            os.system(f"aws s3 sync s3://{bucket} '{local_dir}'")
        elif direction == "up":
            os.system(f"aws s3 sync '{local_dir}' s3://{bucket}")
        else:
            os.system(f"aws s3 sync s3://{bucket} '{local_dir}'")
            os.system(f"aws s3 sync '{local_dir}' s3://{bucket}")

    wlogger.info("run_sync completed")

if __name__ == "__main__":
    wlogger.info("Starting S3 File Watcher")
    #run every 15 mins by default
    delay = os.getenv('DELAY', 900)
    while True:
        run_sync()
        wlogger.info(f"Sleeping for {delay} seconds")
        time.sleep(delay)
