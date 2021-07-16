package file

import (
	"errors"
	"fmt"
	"io/ioutil"
	"math"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

// ListOptions is configuration for the ListFiles method
type ListOptions struct {
	ShowHidden bool
}

// GetOptions is configuration for the GetContents method
type GetOptions struct {
	MaxSize int64 // Limit file size to this amount. Anything above this returns an error
}

var FileTooBig = errors.New("file is too big")
var NotAFile = errors.New("path is not a file")
var NotADirectory = errors.New("path is not a directory")
var PathNotExist = errors.New("path does not exist")

// File represents a system file.
type File struct {
	Path         string `json:"path"`
	Name         string `json:"name"`
	Size         int64 `json:"size"`
	Extension    string `json:"extension"`
	ContentType  string `json:"content_type"`
	LastModified time.Time `json:"last_modified"`
	Directory    bool `json:"directory"`
}

// PaginatedFileResponse is a listing of files with pagination info
type PaginatedFileResponse struct {
	Count int `json:"count"`
	TotalCount int `json:"totalCount"`
	Page int `json:"page"`
	Pages int `json:"pages"`
	Files []*File `json:"files"`
	ParentPath string `json:"parentPath"`
}

// ListPaginatedFilesOptions are all of the available options to paginate files
type ListPaginatedFilesOptions struct {
	Path string
	ShowHidden bool
	Page int
	PerPage int
}

// FilePathToParentPath given a path, returns the parent path, assuming a '/' delimiter
// Result does not have a trailing slash.
// -> a/b/c/d would return a/b/c
// -> a/b/c/d/ would return a/b/c
// If path is empty string, it is returned.
// If path is '/' (root) it is returned as is.
// If there is no '/', '/' is returned.
func FilePathToParentPath(path string) string {
	separator := "/"
	if path == "" || path == separator {
		return path
	}

	if strings.HasSuffix(path, "/") {
		path = path[0 : len(path)-1]
	}

	lastIndexOfForwardSlash := strings.LastIndex(path, separator)
	if lastIndexOfForwardSlash <= 0 {
		return separator
	}

	return path[0:lastIndexOfForwardSlash]
}

// FilePathToName returns the name of the file, assuming that "/" denote directories and that the
// file name is after the last "/"
func FilePathToName(path string) string {
	if strings.HasSuffix(path, "/") {
		path = path[:len(path)-1]
	}

	lastSlashIndex := strings.LastIndex(path, "/")
	if lastSlashIndex < 0 {
		return path
	}

	return path[lastSlashIndex+1:]
}


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


// ListFiles returns all of the Files in the directory.
func ListFiles(filePath string, options *ListOptions) ([]*File, error) {
	fileInfo, err := os.Stat(filePath)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, PathNotExist
		}

		return nil, err
	}

	if !fileInfo.IsDir() {
		return nil, NotADirectory
	}


	result := make([]*File, 0)
	err = filepath.Walk(filePath, func(path string, info os.FileInfo, err error) error {
		if filePath == path {
			return nil
		}

		if !options.ShowHidden && strings.HasPrefix(info.Name(), ".") {
			return nil
		}

		extension := filepath.Ext(path)
		fileName := info.Name()
		if len(extension) > 0 {
			// Remove period from extension
			extension = extension[1:]
		}

		newFile := File{
			Path:         path,
			Name:         fileName,
			Size:         info.Size(),
			Extension:    extension,
			LastModified: info.ModTime().UTC(),
			Directory:    info.IsDir(),
		}

		result = append(result, &newFile)

		if info.IsDir() {
			return filepath.SkipDir
		}

		return nil
	})

	return result, err
}

// ListPaginatedFiles returns all of the Files in the directory, paginated
func ListPaginatedFiles(filePath string, options *ListPaginatedFilesOptions) (*PaginatedFileResponse, error) {
	fileInfo, err := os.Stat(filePath)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, PathNotExist
		}

		return nil, err
	}

	if !fileInfo.IsDir() {
		return nil, NotADirectory
	}


	result := make([]*File, 0)
	err = filepath.Walk(filePath, func(path string, info os.FileInfo, err error) error {
		if filePath == path {
			return nil
		}

		if !options.ShowHidden && strings.HasPrefix(info.Name(), ".") {
			if info.IsDir() {
				return filepath.SkipDir
			}
			return nil
		}

		extension := filepath.Ext(path)
		fileName := info.Name()
		if len(extension) > 0 {
			// Remove period from extension
			extension = extension[1:]
		}

		newFile := File{
			Path:         path,
			Name:         fileName,
			Size:         info.Size(),
			Extension:    extension,
			LastModified: info.ModTime().UTC(),
			Directory:    info.IsDir(),
		}

		result = append(result, &newFile)

		if info.IsDir() {
			return filepath.SkipDir
		}

		return nil
	})

	sort.SliceStable(result, func(i, j int) bool {
		lhFile := result[i]
		rhFile := result[j]

		if (lhFile.Directory && rhFile.Directory) ||
			(!lhFile.Directory && !rhFile.Directory) {
			return strings.Compare(strings.ToLower(lhFile.Name), strings.ToLower(rhFile.Name)) < 0
		}

		if lhFile.Directory {
			return true
		}

		return false
	})

	start := (options.Page - 1) * options.PerPage
	if start < 0 {
		start = 0
	}

	end := start + options.PerPage
	if end > len(result) {
		end = len(result)
	}
	parts := result[start:end]

	count := len(parts)
	totalCount := len(result)

	response := &PaginatedFileResponse{
		Count: count,
		Page: options.Page,
		Pages: int(math.Ceil(float64(totalCount) / float64(options.PerPage))),
		TotalCount: totalCount,
		Files: parts,
		ParentPath: FilePathToParentPath(filePath),
	}

	return response, err
}

// GetContents returns the contents of the file
func GetContents(path string, options *GetOptions) ([]byte, error) {
	fileInfo, err := os.Stat(path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, PathNotExist
		}

		return nil, err
	}

	if fileInfo.IsDir() {
		return nil, NotAFile
	}

	if options.MaxSize != 0 && options.MaxSize <= fileInfo.Size() {
		return nil, FileTooBig
	}

	return ioutil.ReadFile(path)
}

// PrettyPrintFiles is a utility that prints out files in a neat format, similar to ls on linux
func PrettyPrintFiles(files []*File) string {
	result := ""

	for _, file := range files {
		line := ""
		if file.Directory {
			line += "d "
		} else {
			line += "- "
		}

		line += file.Name + "   "
		line += fmt.Sprintf("%v", file.Size) + "   "

		result += line + "\n"
	}

	return result
}