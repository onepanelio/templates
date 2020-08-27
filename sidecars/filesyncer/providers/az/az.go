package az

import (
	"fmt"
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

	if err := cmd.Run(); err != nil {
		fmt.Printf("[error] %v\n", err)
	}

	if util.Action == util.ActionDownload {
		util.Status.MarkLastDownload()
	}
	if util.Action == util.ActionUpload  {
		util.Status.MarkLastUpload()
	}
	if err := util.SaveSyncStatus(); err != nil {
		fmt.Printf("[error] save sync status: Message %v\n", err)
	}
}
