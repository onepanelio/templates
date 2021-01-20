package s3

import (
	"fmt"
	"log"
	"os/exec"

	"github.com/onepanelio/templates/sidecars/filesyncer/util"
)

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

func Sync(action, prefix, path string) func() {
	return func() {
		// Make sure we don't run more than once sync at a time.
		util.Mux.Lock()
		if util.Syncing {
			util.Mux.Unlock()
			return
		} else {
			util.Syncing = true
			util.Mux.Unlock()
		}

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
		uri := fmt.Sprintf("s3://%v/%v", config.S3.Bucket, prefix)
		if action == util.ActionDownload {
			util.Status.IsDownloading = true
			if nonS3 {
				cmd = util.Command("aws", "s3", "sync", "--endpoint-url", nonS3Endpoint, "--delete", uri, path)
			} else {
				cmd = util.Command("aws", "s3", "sync", "--delete", uri, path)
			}
		}
		if action == util.ActionUpload {
			util.Status.IsUploading = true
			if nonS3 {
				cmd = util.Command("aws", "s3", "--endpoint-url", nonS3Endpoint, "sync", "--delete", path, uri)
			} else {
				cmd = util.Command("aws", "s3", "sync", "--delete", path, uri)
			}
		}
		resolveEnv(config, cmd)

		util.Status.ClearError()

		log.Printf("Running cmd %v\n", cmd.String())

		if err := util.RunCommand(cmd); err != nil {
			util.Status.ReportError(err)
			util.Mux.Lock()
			util.Syncing = false
			util.Mux.Unlock()
			return
		}

		if action == util.ActionDownload {
			util.Status.MarkLastDownload()
		}
		if action == util.ActionUpload {
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
