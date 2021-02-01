package s3

import (
	"fmt"
	"log"
	"os/exec"

	"github.com/onepanelio/templates/sidecars/filesyncer/util"
)

// SyncParameters are all allowed parameters for sync
type SyncParameters struct {
	Action string
	Prefix string
	Path   string
	Delete bool
}

func resolveEnv(config *util.ArtifactRepositoryProviderConfig, cmd *exec.Cmd) {
	accessKey := util.Getenv("AWS_ACCESS_KEY_ID", "")
	if accessKey == "" {
		accessKey = config.S3.AccessKey
	}

	secretKey := util.Getenv("AWS_SECRET_ACCESS_KEY", "")
	if secretKey == "" {
		secretKey = config.S3.SecretKey
	}

	cmd.Env = []string{
		"AWS_ACCESS_KEY_ID=" + accessKey,
		"AWS_SECRET_ACCESS_KEY=" + secretKey,
	}
}

// Sync syncs up/down files to/from object storage
func Sync(params SyncParameters) func() {
	return func() {
		// Make sure we don't run more than once sync at a time.
		util.Mux.Lock()
		if util.Syncing {
			util.Mux.Unlock()
			return
		}
		util.Syncing = true
		util.Mux.Unlock()

		config, err := util.GetArtifactRepositoryConfig()
		if err != nil {
			log.Printf("[error] unable to get artifact repository config")
			return
		}

		nonS3 := config.S3.Endpoint != "s3.amazonaws.com"
		nonS3Endpoint := config.S3.Endpoint
		if nonS3 && config.S3.Insecure {
			nonS3Endpoint = "http://" + nonS3Endpoint
		} else {
			nonS3Endpoint = "https://" + nonS3Endpoint
		}

		var cmd *exec.Cmd
		uri := fmt.Sprintf("s3://%v/%v", config.S3.Bucket, params.Prefix)
		args := []string{"s3", "sync"}
		if params.Action == util.ActionDownload {
			util.Status.IsDownloading = true
			args = append(args, uri, params.Path)
		}
		if params.Action == util.ActionUpload {
			util.Status.IsUploading = true
			args = append(args, params.Path, uri)
		}
		if nonS3 {
			args = append(args, "--endpoint-url", nonS3Endpoint)
		}
		if params.Delete {
			args = append(args, "--delete")
		}
		cmd = util.Command("aws", args...)
		resolveEnv(config, cmd)

		util.Status.ClearError()

		if params.Action == util.ActionDownload {
			log.Printf("Syncing files to Workspace...\n")
		} else {
			log.Printf("Syncing files to object storage...\n")
		}

		log.Printf("Running cmd %v\n", cmd.String())

		if err := util.RunCommand(cmd); err != nil {
			util.Status.ReportError(err)
			util.Mux.Lock()
			util.Syncing = false
			util.Mux.Unlock()
			return
		}

		if params.Action == util.ActionDownload {
			log.Printf("Syncing to Workspace is complete.")
			util.Status.MarkLastDownload()
		}
		if params.Action == util.ActionUpload {
			log.Printf("Syncing to object storage is complete.")
			util.Status.MarkLastUpload()
		}

		if err := util.SaveSyncStatus(); err != nil {
			fmt.Printf("[error] save sync status: Message %v\n", err)
		}

		util.Mux.Lock()
		util.Syncing = false
		util.Mux.Unlock()
	}
}
