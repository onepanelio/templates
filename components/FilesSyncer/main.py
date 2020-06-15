
import os
provider = os.getenv("SYNC_PROVIDER", "aws")
if provider == "aws":
    os.system("python3 s3watcher.py")
elif provider == "gcs":
    pass
