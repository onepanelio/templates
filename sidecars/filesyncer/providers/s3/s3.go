package s3

import (
	"fmt"
	"github.com/onepanelio/templates/sidecars/filesyncer/util"
	"log"
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

	gcp := config.S3.Endpoint != "s3.amazonaws.com"

	var cmd *exec.Cmd
	uri := fmt.Sprintf("s3://%v/%v", util.Bucket, util.Prefix)
	if util.Action == util.ActionDownload {
		if gcp {
			cmd = util.Command("aws", "s3", "sync", "--endpoint-url",  "https://storage.googleapis.com", "--delete", uri, util.Path)
		} else {
			cmd = util.Command("aws", "s3", "sync", "--delete", uri, util.Path)
		}
	}
	if util.Action == util.ActionUpload  {
		if gcp {
			cmd = util.Command("aws", "s3", "--endpoint-url https://storage.googleapis.com", "sync", "--delete", util.Path, uri)
		} else {
			cmd = util.Command("aws", "s3", "sync", "--delete", util.Path, uri)
		}
	}
	resolveEnv(cmd)

	util.Status.ClearError()

	log.Printf("Running cmd %v\n", cmd.String())
	
	if err := util.RunCommand(cmd); err != nil {
		util.Status.ReportError(err)
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
