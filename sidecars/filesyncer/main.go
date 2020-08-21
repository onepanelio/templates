package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"github.com/onepanelio/templates/sidecars/filesyncer/providers/az"
	"github.com/onepanelio/templates/sidecars/filesyncer/providers/gcs"
	"github.com/onepanelio/templates/sidecars/filesyncer/providers/s3"
	"github.com/onepanelio/templates/sidecars/filesyncer/util"
	"github.com/onepanelio/templates/sidecars/filesyncer/util/file"
	"github.com/robfig/cron/v3"
	"io"
	"log"
	"net/http"
	"os"
	"path"
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
	flags.StringVar(&util.Provider, "provider", "s3", "Storage provider: s3 (default), az or gcs")
	flags.StringVar(&util.Path, "path", "", "Path to local directory")
	flags.StringVar(&util.Bucket, "bucket", "", "Bucket or container name")
	flags.StringVar(&util.Prefix, "prefix", "", "Key prefix in bucket or container")
	flags.StringVar(&util.Interval, "interval", "", "Sync interval in seconds")
	flags.StringVar(&util.StatusFilePath, "status-path", path.Join(".status", "status.txt"), "Location of file that keeps track of statistics for file uploads/downloads")
	flags.StringVar(&util.ServerURL, "host", "localhost:8888", "URL that you want the server to run")
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

	go startServer()

	c := cron.New()
	spec := fmt.Sprintf("@every %ss", util.Interval)
	switch util.Provider {
	case "az":
		az.Sync()
		c.AddFunc(spec, az.Sync)
	case "gcs":
		gcs.Sync()
		c.AddFunc(spec, gcs.Sync)
	case "s3":
		fallthrough
	default:
		s3.Sync()
		c.AddFunc(spec, s3.Sync)
	}

	c.Run()
}

// getSyncStatus returns the util.Status in JSON form
// If there is no content, a 204 is returned
func getSyncStatus(w http.ResponseWriter, r *http.Request) {
	if util.Status.Empty() {
		w.WriteHeader(http.StatusNoContent)
		return
	} else {
		data, err := json.Marshal(util.Status)
		if err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
		w.Header().Set("content-type", "application/json")
		if _, err := io.WriteString(w, string(data)); err != nil {
			fmt.Printf("[error] %v\n", err)
		}
	}
}

// startServer starts a server that provides information about the file sync status.
func startServer() {
	mux := http.NewServeMux()
	mux.HandleFunc("/api/status", getSyncStatus)

	fmt.Printf("Starting server at %s\n", util.ServerURL)
	err := http.ListenAndServe(util.ServerURL, mux)
	log.Printf("%v", err)
}
