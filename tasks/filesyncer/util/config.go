package util

import (
	"errors"
	"fmt"
	"io/ioutil"
	"sigs.k8s.io/yaml"
)

const ConfigLocation = "/etc/onepanel"

// artifactRepositorySecret defines the structure for secret references
type artifactRepositorySecret struct {
	Key  string
	Name string
}

// artifactRepositoryS3Provider defines the structure for s3 config
type artifactRepositoryS3Provider struct {
	KeyFormat       string
	Bucket          string
	Endpoint        string
	Insecure        bool
	Region          string
	AccessKey       string
	SecretKey       string
	AccessKeySecret artifactRepositorySecret
	SecretKeySecret artifactRepositorySecret
}

// artifactRepositoryGCSProvider defines the structure for gcs config
type artifactRepositoryGCSProvider struct {
	KeyFormat               string
	Bucket                  string
	Endpoint                string
	Insecure                bool
	ServiceAccountKeyPath   string
	ServiceAccountKeySecret artifactRepositorySecret
}

// artifactRepositoryProviderConfig defines the structure for artifactRepository config
type artifactRepositoryProviderConfig struct {
	S3  *artifactRepositoryS3Provider
	GCS *artifactRepositoryGCSProvider
}

func injectS3Credentials(config *artifactRepositoryProviderConfig) error {
	accessKey, err := ioutil.ReadFile(fmt.Sprintf("%v/%v", ConfigLocation, config.S3.AccessKeySecret.Key))
	if err != nil {
		return err
	}

	secretKey, err := ioutil.ReadFile(fmt.Sprintf("%v/%v", ConfigLocation, config.S3.SecretKeySecret.Key))
	if err != nil {
		return err
	}

	config.S3.AccessKey = string(accessKey)
	config.S3.SecretKey = string(secretKey)

	return nil
}

func GetArtifactRepositoryConfig() (*artifactRepositoryProviderConfig, error) {
	content, err := ioutil.ReadFile(ConfigLocation + "/artifactRepository")
	if err != nil {
		return nil, err
	}

	var config *artifactRepositoryProviderConfig
	if yaml.Unmarshal(content, &config); err != nil {
		return nil, err
	}

	if config.S3 != nil {
		injectS3Credentials(config)
	} else if config.GCS != nil {
		config.GCS.ServiceAccountKeyPath = fmt.Sprintf("%v/%v", ConfigLocation, config.GCS.ServiceAccountKeySecret.Key)
	} else {
		return nil, errors.New("invalid configuration")
	}

	return config, nil
}