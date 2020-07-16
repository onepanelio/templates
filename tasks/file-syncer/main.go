package main

import (
	"flag"
	"github.com/onepanelio/templates/tasks/file-syncer/providers/s3"
	"github.com/onepanelio/templates/tasks/file-syncer/util"
	"github.com/robfig/cron/v3"
	"log"
)

func init() {
	flag.StringVar(&util.Provider, "provider", "", "Storage provider: s3 or gcs")
	flag.StringVar(&util.Path, "path", "", "Path to local directory")
	flag.StringVar(&util.StorageURI, "storage-uri", "", "Storage URI, example: s3://<bucket-name>")
	flag.StringVar(&util.Direction, "direction", "", "Sync direction: up or down")

	flag.Parse()
}

func main() {
	if util.Provider == "" {
		util.Provider = util.Getenv("FS_STORAGE_PROVIDER", "")
	}
	if util.Provider == "" {
		log.Println("No storage provider was set, defaulting to s3.")
	}

	if util.Direction == "" {
		util.Direction = util.Getenv("FS_DIRECTION", "")
	}
	if util.Direction == "" {
		log.Fatalln("Direction is required")
	}

	if util.Path == "" {
		util.Path = util.Getenv("FS_PATH", "")
	}
	if util.Path == "" {
		log.Fatalln("Path is required")
	}

	if util.StorageURI == "" {
		util.StorageURI = util.Getenv("FS_STORAGE_URI", "")
	}
	if util.StorageURI == "" {
		log.Fatalln("Storage URI is required")
	}

	c := cron.New()
	switch util.Provider {
	case "s3":
		fallthrough
	default:
		c.AddFunc("@every 5s", s3.Sync)
	}
	c.Run()
}
