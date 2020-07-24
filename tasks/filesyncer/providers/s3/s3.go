package s3

import (
	"fmt"
	"github.com/onepanelio/templates/tasks/file-syncer/util"
	"os/exec"
)

func resolveEnv(cmd *exec.Cmd) {
	accessKey := util.Getenv("AWS_ACCESS_KEY_ID", "")
	if accessKey ==  "" {
		accessKey = util.Config.S3.AccessKey
	}

	secretKey := util.Getenv("AWS_SECRET_ACCESS_KEY", "")
	if secretKey == "" {
		secretKey = util.Config.S3.SecretKey
	}

	cmd.Env = []string{
		"AWS_ACCESS_KEY_ID=" + accessKey,
		"AWS_SECRET_ACCESS_KEY=" + secretKey,
	}
}

func Sync() {
	var cmd *exec.Cmd
	uri := fmt.Sprintf("s3://%v/%v", util.Bucket, util.Prefix)
	if util.Action == util.ActionDownload {
		cmd = util.Command("aws", "s3", "sync", "--delete", uri, util.Path)
	}
	if util.Action == util.ActionUpload  {
		cmd = util.Command("aws", "s3", "sync", "--delete", util.Path, uri)
	}
	resolveEnv(cmd)
	cmd.Run()
}
