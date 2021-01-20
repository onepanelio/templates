package main

import (
	"flag"
	"fmt"
	"os"
	"path"
	"time"

	"github.com/onepanelio/templates/sidecars/filesyncer/providers/s3"
	"github.com/onepanelio/templates/sidecars/filesyncer/server"
	"github.com/onepanelio/templates/sidecars/filesyncer/util"
	"github.com/onepanelio/templates/sidecars/filesyncer/util/file"
	"github.com/robfig/cron/v3"
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
		fmt.Println("   server\t act as file server sidecar")
		os.Exit(1)
	}
	fmt.Printf("Usage:\n   %s %s [options]\n\n", os.Args[0], util.Action)
	fmt.Println("The options are:")
	flags.PrintDefaults()
	os.Exit(1)
}

func main() {
	if len(os.Args) < 2 || os.Args[1] != util.ActionUpload && os.Args[1] != util.ActionDownload && os.Args[1] != util.ActionServer {
		help("Please indicate if this is an 'upload' or 'download' action", nil)
	}
	util.Action = os.Args[1]

	flags := flag.NewFlagSet(util.Action, flag.ExitOnError)
	flags.StringVar(&util.Path, "path", "", "Path to local directory")
	flags.StringVar(&util.Bucket, "bucket", "", "Bucket or container name")
	flags.StringVar(&util.Prefix, "prefix", "", "Key prefix in bucket or container")
	flags.StringVar(&util.Interval, "interval", "", "Sync interval in seconds")
	flags.StringVar(&util.StatusFilePath, "status-path", path.Join(".status", "status.json"), "Location of file that keeps track of statistics for file uploads/downloads")
	flags.StringVar(&util.ServerURL, "host", "localhost:8888", "URL that you want the server to run")
	flags.StringVar(&util.ServerURLPrefix, "server-prefix", "", "Prefix for the server api urls")
	flags.StringVar(&util.ConfigLocation, "config-path", "/etc/onepanel", "The location of config files. A file named artifactRepository is expected to be here.")
	flags.DurationVar(&util.InitialDelay, "initial-delay", 30*time.Second, "Initial delay before program starts syncing files. Acceptable values are: 30s")
	flags.Parse(os.Args[2:])

	if err := file.CreateIfNotExist(util.StatusFilePath); err != nil {
		fmt.Printf("[error] Unable to create status file path '%v'. Message: %v\n", util.StatusFilePath, err)
		return
	}

	status, err := util.LoadSyncStatus()
	if err != nil {
		fmt.Printf("[error] Unable to load status file data. Message: %v\n", err)
		return
	}
	util.Status = status

	config, err := util.GetArtifactRepositoryConfig()
	if err != nil {
		help("artifact repository config was not found", flags)
	}
	if config == nil {
		fmt.Println("Unknown error loading ArtifactRepositoryConfig")
		return
	}

	util.Config = config

	if util.Bucket == "" {
		util.Bucket = util.Getenv("FS_BUCKET", "")
	}
	if util.Bucket == "" {
		if config.S3 != nil {
			util.Bucket = config.S3.Bucket
		}
	}
	if util.Bucket == "" {
		help("bucket or container name is required", flags)
	}

	// If action is server, we just run the server
	if util.Action == util.ActionServer {
		server.StartServer()
		return
	}

	if util.Path == "" {
		util.Path = util.Getenv("FS_PATH", "")
	}
	if util.Path == "" {
		help("path is required", flags)
	}

	if util.Prefix == "" {
		util.Prefix = util.Getenv("FS_PREFIX", "")
	}

	if util.Interval == "" {
		util.Interval = util.Getenv("FS_INTERVAL", "300")
	}

	go server.StartServer()

	fmt.Printf("Sleeping for  %v\n", util.InitialDelay)
	time.Sleep(util.InitialDelay)
	fmt.Printf("Done sleeping.\n")

	c := cron.New()
	spec := fmt.Sprintf("@every %ss", util.Interval)
	go s3.Sync(util.Action, util.Bucket, util.Prefix, util.Path)()
	c.AddFunc(spec, s3.Sync(util.Action, util.Bucket, util.Prefix, util.Path))

	c.Run()
}
