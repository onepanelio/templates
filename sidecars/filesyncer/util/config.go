package util

import (
	"errors"
	"fmt"
	"io/ioutil"
	"path"

	"sigs.k8s.io/yaml"
)

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

// ArtifactRepositoryProviderConfig defines the structure for artifactRepository config
type ArtifactRepositoryProviderConfig struct {
	S3 *artifactRepositoryS3Provider
}

func injectS3Credentials(config *ArtifactRepositoryProviderConfig) error {
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

func GetArtifactRepositoryConfig() (*ArtifactRepositoryProviderConfig, error) {
	configFilePath := path.Join(ConfigLocation, "artifactRepository")
	content, err := ioutil.ReadFile(configFilePath)
	if err != nil {
		return nil, err
	}

	var config *ArtifactRepositoryProviderConfig
	if err = yaml.Unmarshal(content, &config); err != nil {
		return nil, err
	}
	if config == nil {
		return nil, fmt.Errorf("config file path: '%v' does not have any content", configFilePath)
	}

	if config.S3 != nil {
		injectS3Credentials(config)
	} else {
		return nil, errors.New("invalid configuration")
	}

	return config, nil
}
