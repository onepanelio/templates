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
	flag.StringVar(&util.Direction, "direction", "", "Sync direction: up, down, both")

	flag.Parse()
}

func main() {
	provider := util.Provider
	if provider == "" {
		provider = util.Getenv("FS_STORAGE_PROVIDER", "")
	}
	if provider == "" {
		log.Println("No storage provider was set, defaulting to s3.")
	}

	direction := util.Direction
	if direction == "" {
		direction = util.Getenv("FS_STORAGE_URI", "both")
	}
	if direction == "" {
		log.Println("No sync direction was set, defaulting to 'both'.")
	}

	path := util.Path
	if path == "" {
		path = util.Getenv("FS_PATH", "")
	}
	if path == "" {
		log.Fatalln("Path is required")
	}

	storageURI := util.StorageURI
	if storageURI == "" {
		storageURI = util.Getenv("FS_STORAGE_URI", "")
	}
	if storageURI == "" {
		log.Fatalln("Storage URI is required")
	}

	c := cron.New()
	switch provider {
	case "s3":
		fallthrough
	default:
		if direction == "up" || direction == "both" {
			c.AddFunc("@every 5s", s3.Upload)
		}
		if direction == "down" || direction == "both" {
			c.AddFunc("@every 5s", s3.Download)
		}
	}
	c.Run()
}
