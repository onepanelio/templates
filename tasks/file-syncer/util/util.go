package util

import "os"

var (
	Provider	string
	Path 		string
	StorageURI 	string
	Direction	string
)

func Getenv(key, value string) string {
	env := os.Getenv(key)
	if env == "" {
		env = value
	}

	return env
}