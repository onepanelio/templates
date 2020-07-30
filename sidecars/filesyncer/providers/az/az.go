package az

import (
	"github.com/onepanelio/templates/sidecars/filesyncer/util"
	"os/exec"
)

func Sync() {
	var cmd *exec.Cmd
	if util.Action == util.ActionDownload {
		cmd = util.Command("az", "storage", "blob", "download-batch", "-s", util.Bucket, "--pattern", util.Prefix + "/*", "-d", util.Path)
	}
	if util.Action == util.ActionUpload  {
		cmd = util.Command("az", "storage", "blob", "upload-batch", "-s", util.Path, "-d", util.Bucket, "--pattern", util.Prefix + "/*",)
	}
	cmd.Run()
}
