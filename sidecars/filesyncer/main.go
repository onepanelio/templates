package main

import (
	"flag"
	"fmt"
	"github.com/onepanelio/templates/sidecars/filesyncer/providers/az"
	"github.com/onepanelio/templates/sidecars/filesyncer/providers/gcs"
	"github.com/onepanelio/templates/sidecars/filesyncer/providers/s3"
	"github.com/onepanelio/templates/sidecars/filesyncer/util"
	"github.com/robfig/cron/v3"
	"os"
)

func help(error string, flags *flag.FlagSet) {
	if error != "" {
		fmt.Printf("Error: %v\n\n", error)
	}
	if flags == nil {
		fmt.Printf("Usage:\n \t %s <command> [arguments]\n\n", os.Args[0])
		fmt.Print("The commands are:\n\n")
		fmt.Println("   download\t download files from bucket or container")
		fmt.Println("   upload\t upload files to bucket or container")
		os.Exit(1)
	}
	fmt.Printf("Usage:\n   %s %s [options]\n\n", os.Args[0], util.Action)
	fmt.Println("The options are:")
	flags.PrintDefaults()
	os.Exit(1)
}

func main() {
	if len(os.Args) < 2 || os.Args[1] != util.ActionUpload && os.Args[1] != util.ActionDownload {
		help("Please indicate if this is an 'upload' or 'download' action", nil)
	}
	util.Action = os.Args[1]

	flags := flag.NewFlagSet(util.Action, flag.ExitOnError)
	flags.StringVar(&util.Provider, "provider", "", "Storage provider: s3 (default), az or gcs")
	flags.StringVar(&util.Path, "path", "", "Path to local directory")
	flags.StringVar(&util.Bucket, "bucket", "", "Bucket or container name")
	flags.StringVar(&util.Prefix, "prefix", "", "Key prefix in bucket or container")
	flags.StringVar(&util.Interval, "interval", "", "Sync interval in seconds")
	flags.Parse(os.Args[2:])

	config, err := util.GetArtifactRepositoryConfig()
	if err != nil {
		help("artifact repository config was not found", flags)
	}
	util.Config = config

	if util.Path == "" {
		util.Path = util.Getenv("FS_PATH", "")
	}
	if util.Path == "" {
		help("path is required", flags)
	}

	if util.Bucket == "" {
		util.Bucket = util.Getenv("FS_BUCKET", "")
	}
	if util.Bucket == "" {
		if config.S3 != nil {
			util.Bucket = config.S3.Bucket
		}
		if config.GCS != nil {
			util.Bucket = config.GCS.Bucket
		}
	}
	if util.Bucket == "" {
		help("bucket or container name is required", flags)
	}

	if util.Provider == "" {
		util.Provider = util.Getenv("FS_PROVIDER", "")
	}
	if util.Provider == "" {
		if config.S3 != nil {
			util.Provider = "s3"
		}
		if config.GCS != nil {
			util.Provider = "gcs"
		}
	}

	if util.Prefix == "" {
		util.Prefix = util.Getenv("FS_PREFIX", "")
	}

	if util.Interval == "" {
		util.Interval = util.Getenv("FS_INTERVAL", "300")
	}

	c := cron.New()
	spec := fmt.Sprintf("@every %ss", util.Interval)
	switch util.Provider {
	case "az":
		c.AddFunc(spec, az.Sync)
	case "gcs":
		c.AddFunc(spec, gcs.Sync)
	case "s3":
		fallthrough
	default:
		c.AddFunc(spec, s3.Sync)
	}
	c.Run()
}
