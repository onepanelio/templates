package az

import (
	"fmt"
	"github.com/onepanelio/templates/sidecars/filesyncer/util"
	"os/exec"
)

func Sync() {
	// Make sure we don't run more than once sync at a time.
	util.Mux.Lock()
	if util.Syncing {
		util.Mux.Unlock()
		return
	} else {
		util.Syncing = true
		util.Mux.Unlock()
	}

	var cmd *exec.Cmd
	if util.Action == util.ActionDownload {
		cmd = util.Command("az", "storage", "blob", "download-batch", "-s", util.Bucket, "--pattern", util.Prefix + "/*", "-d", util.Path)
	}
	if util.Action == util.ActionUpload  {
		cmd = util.Command("az", "storage", "blob", "upload-batch", "-s", util.Path, "-d", util.Bucket, "--pattern", util.Prefix + "/*",)
	}

	util.Status.ClearError()
	if err := util.RunCommand(cmd); err != nil {
		util.Status.ReportError(err)
		util.Mux.Lock()
		util.Syncing = false
		util.Mux.Unlock()
		return
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

	util.Mux.Lock()
	util.Syncing = false
	util.Mux.Unlock()
}
