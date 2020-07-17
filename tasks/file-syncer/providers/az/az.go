package az

import (
	"github.com/onepanelio/templates/tasks/file-syncer/util"
	"os/exec"
)

func Sync() {
	var cmd *exec.Cmd
	if util.Action == util.ActionDownload {
		cmd = util.Command("az", "sync", "-d", "-r", util.Bucket, util.Path)
	}
	if util.Action == util.ActionUpload  {
		cmd = util.Command("az", "sync", "-d", "-r", util.Path, util.Bucket)
	}
	cmd.Run()
}
