package s3

import (
	"github.com/onepanelio/templates/tasks/file-syncer/util"
	"log"
	"os"
	"os/exec"
)

func Upload() {
	cmd := exec.Command("aws", "s3", "sync", util.Path, util.StorageURI)
	cmd.Stdout = os.Stdout
	if err := cmd.Run(); err != nil {
		log.Println(err)
	}
}

func Download() {
	cmd := exec.Command("aws", "s3", "sync", util.StorageURI, util.Path)
	cmd.Stdout = os.Stdout
	if err := cmd.Run(); err != nil {
		log.Println(err)
	}
}