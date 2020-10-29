package util

import (
	"encoding/json"
	"io/ioutil"
	"strings"
	"time"
)

// SyncStatus keeps track of the timestamps when the last file operation occurred
type SyncStatus struct {
	LastUpload             *time.Time `json:"lastUpload"`
	LastDownload           *time.Time `json:"lastDownload"`
	BackCompatLastDownload *time.Time `json:"LastDownload"`
	BackCompatLastUpload   *time.Time `json:"LastUpload"`
	IsDownloading          bool       `json:"isDownloading"`
	IsUploading            bool       `json:"isUploading"`
	Error                  *string    `json:"error"`
	PreviousError          *string    `json:"previousError"`
}

// MarkLastUpload sets the last upload time to now
func (s *SyncStatus) MarkLastUpload() {
	now := time.Now().UTC()
	s.LastUpload = &now
	s.BackCompatLastUpload = &now
	s.IsUploading = false
}

// MarkLastDownload sets the last download time to now
func (s *SyncStatus) MarkLastDownload() {
	now := time.Now().UTC()
	s.LastDownload = &now
	s.BackCompatLastDownload = &now
	s.IsDownloading = false
}

// ReportError sets the Error field on SyncStatus
// if there is already an error, the current error is moved into PreviousError
func (s *SyncStatus) ReportError(err error) {
	if s.Error != nil {
		s.PreviousError = s.Error
	}

	errMsg := err.Error()
	if strings.Contains(errMsg, "No space left on device") {
		errMsg = "Not enough space on machine"
	}

	s.Error = &errMsg
}

// ClearError clears out the current error. It is moved to previous error.
func (s *SyncStatus) ClearError() {
	if s.Error != nil {
		s.PreviousError = s.Error
	}

	s.Error = nil
}

// ClearErrors clears out all of the errors including current and previous
func (s *SyncStatus) ClearErrors() {
	s.Error = nil
	s.PreviousError = nil
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
