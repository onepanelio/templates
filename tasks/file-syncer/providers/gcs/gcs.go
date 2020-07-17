package gcs

import (
	"fmt"
	"github.com/onepanelio/templates/tasks/file-syncer/util"
	"os/exec"
)

func Sync() {
	var cmd *exec.Cmd
	uri := fmt.Sprintf("gs://%v/%v", util.Bucket, util.Prefix)
	if util.Action == util.ActionDownload {
		cmd = util.Command("gsutil", "-m", "rsync", "-d", "-r", uri, util.Path)
	}
	if util.Action == util.ActionUpload {
		cmd = util.Command("gsutil", "-m", "rsync", "-d", "-r", util.Path, uri)
	}
	cmd.Run()
}
