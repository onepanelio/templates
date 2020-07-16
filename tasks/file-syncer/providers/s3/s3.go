package s3

import (
	"github.com/onepanelio/templates/tasks/file-syncer/util"
	"os/exec"
)

func Sync() {
	var cmd *exec.Cmd
	if util.Direction == "down" {
		cmd = util.Command("aws", "s3", "sync", "--delete", util.StorageURI, util.Path)
	}
	if util.Direction == "up"  {
		cmd = util.Command("aws", "s3", "sync", "--delete", util.Path, util.StorageURI)
	}
	cmd.Run()
}
