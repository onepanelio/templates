package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"path"
	"strings"
	"time"

	"github.com/onepanelio/templates/sidecars/filesyncer/providers/s3"
	"github.com/onepanelio/templates/sidecars/filesyncer/util"
	"github.com/onepanelio/templates/sidecars/filesyncer/util/file"
	"github.com/robfig/cron/v3"
)

type SyncRequest struct {
	Direction string
	Prefix    string
	Path      string
}

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
		startServer()
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

	go startServer()

	fmt.Printf("Sleeping for  %v\n", util.InitialDelay)
	time.Sleep(util.InitialDelay)
	fmt.Printf("Done sleeping.\n")

	c := cron.New()
	spec := fmt.Sprintf("@every %ss", util.Interval)
	go s3.Sync()
	c.AddFunc(spec, s3.Sync)

	c.Run()
}

// routeSyncStatus reads the request and routes it to either a GET or PUT endpoint based on the method
// 405 is returned if it is neither a GET nor a PUT
func routeSyncStatus(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")

	if r.Method == "" || r.Method == "GET" {
		getSyncStatus(w, r)
	} else if r.Method == "PUT" {
		putSyncStatus(w, r)
	} else {
		w.WriteHeader(405) // not allowed
	}
}

// getSyncStatus returns the util.Status in JSON form
func getSyncStatus(w http.ResponseWriter, r *http.Request) {
	data, err := json.Marshal(util.Status)
	if err != nil {
		log.Printf("[error] marshaling util.Status: %s\n", err)
		w.WriteHeader(http.StatusInternalServerError)
		return
	}
	w.Header().Set("content-type", "application/json")
	if _, err := io.WriteString(w, string(data)); err != nil {
		log.Printf("[error] %s\n", err)
	}
}

// putSyncStatus updates the util.Status with the input values
// all values are overridden
func putSyncStatus(w http.ResponseWriter, r *http.Request) {
	content, err := ioutil.ReadAll(r.Body)
	if err != nil {
		log.Printf("[error] reading sync status put body: %s\n", err)
		w.WriteHeader(http.StatusInternalServerError)
		return
	}

	if err := json.Unmarshal(content, util.Status); err != nil {
		log.Printf("[error] unmarshaling sync status body: %s: %s\n", content, err)
		w.WriteHeader(http.StatusInternalServerError)
		return
	}

	getSyncStatus(w, r)
}

func sync(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		log.Printf("[error] sync request failed: only POST method is allowed\n")
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}

	decoder := json.NewDecoder(r.Body)
	var syncRequest SyncRequest
	err := decoder.Decode(&syncRequest)
	if err != nil {
		log.Printf("[error] sync request failed: %s\n", err)
		w.WriteHeader(http.StatusInternalServerError)
		return
	}

	util.Action = syncRequest.Direction
	util.Prefix = syncRequest.Prefix
	util.Path = syncRequest.Path

	go s3.Sync()

	w.Header().Set("content-type", "application/json")
	io.WriteString(w, "Sync command sent")
}

func handleUnsupportedEndpoint(w http.ResponseWriter, r *http.Request) {
	relativeEndpoint := r.URL.Path
	if strings.HasPrefix(r.URL.Path, util.ServerURLPrefix) {
		relativeEndpoint = r.URL.Path[len(util.ServerURLPrefix):]
	}
	log.Printf("Miss [endpoint] %v. Relative: %v", r.URL.Path, relativeEndpoint)
	log.Printf("RequestURI %v. ServerURLPrefix %v", r.URL.Path, util.ServerURLPrefix)

	w.WriteHeader(http.StatusNotFound)
}

// startServer starts a server that provides information about the file sync status.
func startServer() {
	mux := http.NewServeMux()
	mux.HandleFunc(util.ServerURLPrefix+"/api/status", routeSyncStatus)
	mux.HandleFunc(util.ServerURLPrefix+"/api/sync", sync)
	mux.HandleFunc("/", handleUnsupportedEndpoint)

	fmt.Printf("Starting server at %s. Prefix: %v\n", util.ServerURL, util.ServerURLPrefix)
	err := http.ListenAndServe(util.ServerURL, mux)
	log.Printf("%v", err)
}
