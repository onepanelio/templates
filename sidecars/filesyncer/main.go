package main

import (
	"flag"
	"fmt"
	"os"
	"path"
	"strings"
	"time"

	"github.com/onepanelio/templates/sidecars/filesyncer/providers/s3"
	"github.com/onepanelio/templates/sidecars/filesyncer/server"
	"github.com/onepanelio/templates/sidecars/filesyncer/util"
	"github.com/onepanelio/templates/sidecars/filesyncer/util/file"
	"github.com/robfig/cron/v3"
)

func help(error, action string, flags *flag.FlagSet) {
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
	fmt.Printf("Usage:\n   %s %s [options]\n\n", os.Args[0], action)
	fmt.Println("The options are:")
	flags.PrintDefaults()
	os.Exit(1)
}

func validateBackendFlagValid(backend string) error {
	backendStorages := strings.Split(backend, ",")
	if len(backendStorages) == 0 {
		return fmt.Errorf("unknown configuration for backend flag: '%v'", backend)
	}
	if len(backendStorages) > 2 {
		return fmt.Errorf("unknown configuration for backend flag, more than 2 results")
	}
	for _, backendStorage := range backendStorages {
		if backendStorage != "local-storage" && backendStorage != "object-storage" {
			return fmt.Errorf("unknown backend option: '%v'", backendStorage)
		}
	}

	return nil
}

func parseBackendFlag(backend string) (localStorage, objectStorage bool) {
	backendStorages := strings.Split(backend, ",")

	for _, backendStorage := range backendStorages {
		if backendStorage == "local-storage" {
			localStorage = true
		}

		if backendStorage == "object-storage" {
			objectStorage = true
		}
	}

	return localStorage, objectStorage
}

func main() {
	action := os.Args[1]
	if len(os.Args) < 2 || os.Args[1] != util.ActionUpload && os.Args[1] != util.ActionDownload && os.Args[1] != util.ActionServer {
		help("Please indicate if this is an 'upload', 'download', or 'server' action", action, nil)
	}

	var filepath, bucket, prefix, interval, serverURL, serverURLPrefix, backend string
	var initialDelay time.Duration
	flags := flag.NewFlagSet(action, flag.ExitOnError)
	flags.StringVar(&filepath, "path", "", "Path to local directory")
	flags.StringVar(&bucket, "bucket", "", "Bucket or container name")
	flags.StringVar(&prefix, "prefix", "", "Key prefix in bucket or container")
	flags.StringVar(&interval, "interval", "", "Sync interval in seconds")
	flags.StringVar(&util.StatusFilePath, "status-path", path.Join(".status", "status.json"), "Location of file that keeps track of statistics for file uploads/downloads")
	flags.StringVar(&serverURL, "host", "localhost:8888", "URL that you want the server to run")
	flags.StringVar(&serverURLPrefix, "server-prefix", "", "Prefix for the server api urls")
	flags.StringVar(&util.ConfigLocation, "config-path", "/etc/onepanel", "The location of config files. A file named artifactRepository is expected to be here.")
	flags.DurationVar(&initialDelay, "initial-delay", 30*time.Second, "Initial delay before program starts syncing files. Acceptable values are: 30s")
	flags.StringVar(&backend, "backend", "local-storage,object-storage", "The file API you want to expose. Defaults to be local and object storage.")
	flags.Parse(os.Args[2:])


	if err := validateBackendFlagValid(backend); err != nil {
		fmt.Printf("error: %v", err)
		return
	}

	localStorage, objectStorage := parseBackendFlag(backend)

	serverConfig := server.Config{
		URL:       serverURL,
		URLPrefix: serverURLPrefix,
	}

	if action == util.ActionServer && localStorage && !objectStorage {
		server.StartServer(serverConfig)
		return
	}

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
		help("artifact repository config was not found", action, flags)
	}
	if config == nil {
		fmt.Println("Unknown error loading ArtifactRepositoryConfig")
		return
	}

	if action == util.ActionServer  {
		server.StartServer(serverConfig)
		return
	}

	if filepath == "" {
		filepath = util.Getenv("FS_PATH", "")
	}
	if filepath == "" {
		help("path is required", action, flags)
	}

	if prefix == "" {
		prefix = util.Getenv("FS_PREFIX", "")
	}

	if interval == "" {
		interval = util.Getenv("FS_INTERVAL", "300")
	}

	go server.StartServer(serverConfig)

	fmt.Printf("Sleeping for  %v\n", initialDelay)
	time.Sleep(initialDelay)
	fmt.Printf("Done sleeping.\n")

	c := cron.New()
	spec := fmt.Sprintf("@every %ss", interval)
	params := s3.SyncParameters{
		Action: action,
		Prefix: prefix,
		Path:   filepath,
		Delete: true,
	}
	go s3.Sync(params)()
	c.AddFunc(spec, s3.Sync(params))

	c.Run()
}
