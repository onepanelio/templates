package util

import (
	"os"
	"os/exec"
)

var (
	Provider string
	Path     string
	Bucket   string
	Prefix   string
	Action   string
	Config 	 *artifactRepositoryProviderConfig
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