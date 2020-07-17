package main

import (
	"flag"
	"github.com/onepanelio/templates/tasks/file-syncer/providers/gcs"
	"github.com/onepanelio/templates/tasks/file-syncer/providers/s3"
	"github.com/onepanelio/templates/tasks/file-syncer/util"
	"github.com/robfig/cron/v3"
	"log"
	"os"
)

func main() {
	if os.Args[1] != util.ActionUpload && os.Args[1] != util.ActionDownload {
		log.Fatalln("Please indicate if this is an 'upload' or 'download' action")
	}
	util.Action = os.Args[1]

	flags := flag.NewFlagSet(util.Action, flag.ExitOnError)
	flags.StringVar(&util.Provider, "provider", "", "Storage provider: s3 or gcs")
	flags.StringVar(&util.Path, "path", "", "Path to local directory")
	flags.StringVar(&util.Bucket, "bucket", "", "Bucket or container name")
	flags.StringVar(&util.Prefix, "prefix", "", "Key prefix in bucket or container")
	flags.Parse(os.Args[2:])

	if util.Provider == "" {
		util.Provider = util.Getenv("FS_STORAGE_PROVIDER", "")
	}
	if util.Provider == "" {
		log.Println("No storage provider was set, defaulting to s3.")
	}

	if util.Path == "" {
		util.Path = util.Getenv("FS_PATH", "")
	}
	if util.Path == "" {
		log.Fatalln("Path is required")
	}

	if util.Bucket == "" {
		util.Bucket = util.Getenv("FS_BUCKET", "")
	}
	if util.Bucket == "" {
		log.Fatalln("Bucket or container name is required")
	}

	if util.Prefix == "" {
		util.Prefix = util.Getenv("FS_PREFIX", "")
	}

	c := cron.New()
	switch util.Provider {
	case "gcs":
		c.AddFunc("@every 5s", gcs.Sync)
	case "s3":
		fallthrough
	default:
		c.AddFunc("@every 5s", s3.Sync)
	}
	c.Run()
}
