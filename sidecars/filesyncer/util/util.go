package util

import (
	"fmt"
	"io/ioutil"
	"os"
	"os/exec"
	"sync"
)

var (
	ConfigLocation string
	StatusFilePath string      // where we keep statistics about file uploads/downloads
	Status         *SyncStatus // keeps track of the status of file uploads/downloads
	Syncing        = false
	Mux            sync.Mutex
	JustServer     bool // if true, no syncing is done, just the information server is run. Mostly used for debugging/testing
)

const (
	ActionUpload   = "upload"
	ActionDownload = "download"
	ActionServer   = "server"
)

// Getenv loads the key from the environment, if not found, return defaultValue instead.
func Getenv(key, defaultValue string) string {
	env := os.Getenv(key)
	if env == "" {
		env = defaultValue
	}

	return env
}

func Command(name string, arg ...string) *exec.Cmd {
	cmd := exec.Command(name, arg...)
	cmd.Stdout = os.Stdout

	return cmd
}

// RunCommand runs the command and returns the stderr if there is one instead of the wrapper error.
func RunCommand(cmd *exec.Cmd) error {
	stdErr, err := cmd.StderrPipe()
	if err != nil {
		return err
	}

	if err := cmd.Start(); err != nil {
		return err
	}

	errMessage, err := ioutil.ReadAll(stdErr)
	if err != nil {
		return err
	}

	if err := cmd.Wait(); err != nil {
		fmt.Printf("%s", errMessage)
		return fmt.Errorf("%s", errMessage)
	}

	return nil
}
