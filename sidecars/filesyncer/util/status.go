package util

import (
	"encoding/json"
	"io/ioutil"
	"time"
)

// SyncStatus keeps track of the timestamps when the last file operation occurred
type SyncStatus struct {
	LastUpload *time.Time
	LastDownload *time.Time
}

// MarkLastUpload sets the last upload time to now
func (s *SyncStatus) MarkLastUpload() {
	now := time.Now().UTC()
	s.LastUpload = &now
}

// MarkLastDownload sets the last download time to now
func (s *SyncStatus) MarkLastDownload() {
	now := time.Now().UTC()
	s.LastDownload = &now
}

// Empty returns true if s is nil or none of it's fields are set
func (s *SyncStatus) Empty() bool {
	return s == nil || (s.LastDownload == nil && s.LastUpload == nil)
}

// LoadSyncStatus will attempt to load the SyncStatus from the file stored at
// util.StatusFilPath. It attempts to load it in JSON format.
func LoadSyncStatus() (*SyncStatus, error) {
	data, err := ioutil.ReadFile(StatusFilePath)
	if err != nil {
		return nil, err
	}

	result := &SyncStatus{}
	if len(data) == 0 {
		return result, nil
	}
	if err := json.Unmarshal(data, result); err != nil {
		return nil, err
	}

	return result, nil
}

// SaveSyncStatus will save the SyncStatus in util.Status in JSON to the file at util.StatusFilePath
func SaveSyncStatus() error {
	if Status == nil {
		return nil
	}

	data, err := json.Marshal(Status)
	if err != nil {
		return err
	}

	return ioutil.WriteFile(StatusFilePath, data, 0)
}

