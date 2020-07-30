package gcs

import (
	"fmt"
	"github.com/onepanelio/templates/sidecars/filesyncer/util"
	"os/exec"
)



func Sync() {
	var cmd *exec.Cmd

	// Activate service account
	cmd = util.Command("gcloud", "auth", "activate-service-account", "--key-file", util.Config.GCS.ServiceAccountKeyPath)
	cmd.Run()

	// Sync to or from bucket
	uri := fmt.Sprintf("gs://%v/%v", util.Bucket, util.Prefix)
	if util.Action == util.ActionDownload {
		cmd = util.Command("gsutil", "-m", "rsync", "-d", "-r", uri, util.Path)
	}
	if util.Action == util.ActionUpload {
		cmd = util.Command("gsutil", "-m", "rsync", "-d", "-r", util.Path, uri)
	}
	cmd.Run()
}
