package util

import (
	"os"
	"os/exec"
	"time"
)

var (
	Provider string
	Path     string
	Bucket   string
	Prefix   string
	Action   string
	Interval string
	Config 	 *artifactRepositoryProviderConfig
	StatusFilePath string // where we keep statistics about file uploads/downloads
	ServerURL string // where we run the server. E.g. localhost:8888
	ServerURLPrefix string // prefix for all the api endpoints
	Status *SyncStatus // keeps track of the status of file uploads/downloads
	InitialDelay time.Duration // initial delay before app starts cron to sync files. In seconds.
)

const (
	ActionUpload = "upload"
	ActionDownload = "download"
)

func Getenv(key, value string) string {
	env := os.Getenv(key)
	if env == "" {
		env = value
	}

	return env
}

func Command(name string, arg ...string) *exec.Cmd {
	cmd := exec.Command(name, arg...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	return cmd
}