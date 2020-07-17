package s3

import (
	"fmt"
	"github.com/onepanelio/templates/tasks/file-syncer/util"
	"os/exec"
)

func Sync() {
	var cmd *exec.Cmd
	uri := fmt.Sprintf("s3://%v/%v", util.Bucket, util.Prefix)
	if util.Action == util.ActionDownload {
		cmd = util.Command("aws", "s3", "sync", "--delete", uri, util.Path)
	}
	if util.Action == util.ActionUpload  {
		cmd = util.Command("aws", "s3", "sync", "--delete", util.Path, uri)
	}
	cmd.Run()
}
