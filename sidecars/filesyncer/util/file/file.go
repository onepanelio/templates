package file

import (
	"fmt"
	"os"
	"strings"
)

// exists returns whether the given file or directory exists
func Exists(path string) (bool, error) {
	_, err := os.Stat(path)
	if err == nil {
		return true, nil
	}

	if os.IsNotExist(err) {
		return false, nil
	}

	return true, err
}

// CreateIfNotExist will create the file at the specific path if it does not exist.
// It will also create any folders along the way.
func CreateIfNotExist(path string) error {
	parts := strings.Split(path, string(os.PathSeparator))
	partialPath := ""

	for i := 0; i < len(parts); i++ {
		if i != 0 {
			partialPath += string(os.PathSeparator)
		}

		partialPath += parts[i]

		exists, err := Exists(partialPath)
		if err != nil {
			return fmt.Errorf("unable to check if %v file exists: %v", path, err.Error())
		}
		if exists {
			continue
		}

		if i == (len(parts) - 1) {
			if _, err := os.Create(partialPath); err != nil {
				return fmt.Errorf("unable to create %v file: %v", partialPath, err.Error())
			}
		} else {
			if err := os.Mkdir(partialPath, 0777); err != nil {
				return fmt.Errorf("unable to create directory '%v'. Message: %v", partialPath, err)
			}
		}
	}

	return nil
}

// Delete a file if it exists. If it doesn't, nothing happens.
// Returns if the file existed. If there was an error, existed is set to false, and err is set.
func DeleteIfExists(path string) (existed bool, err error) {
	existed, err = Exists(path)
	if err != nil {
		return false, err
	}

	if !existed {
		return
	}

	if err := os.Remove(path); err != nil {
		return existed, err
	}

	return
}
