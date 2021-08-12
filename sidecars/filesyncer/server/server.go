package server

import (
	"context"
	"encoding/json"
	"fmt"
	"github.com/onepanelio/templates/sidecars/filesyncer/util/file"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"net/url"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"syscall"
	"time"

	"github.com/justinas/alice"
	"github.com/onepanelio/templates/sidecars/filesyncer/providers/s3"
	"github.com/onepanelio/templates/sidecars/filesyncer/util"
)

// Config is used for server configuration
type Config struct {
	URL       string
	URLPrefix string
}

// ServerError represents an error that happened while processing a request and is returned to the client
type ServerError struct {
	Message string `json:"message"`
}

// NewServerError creates a ServerError with a given message
func NewServerError(message string) *ServerError {
	return &ServerError{
		Message: message,
	}
}

func writeJson(w http.ResponseWriter, data interface{}) error {
	resultBytes, err := json.Marshal(data)
	if err != nil {
		log.Printf("error Marshaling json %v", err.Error())
		return err
	}

	if _, err := io.WriteString(w, string(resultBytes)); err != nil {
		log.Printf("error writing json to ResponseWriter %v", err.Error())
		return err
	}

	return nil
}

// routeSyncStatus reads the request and routes it to either a GET or PUT endpoint based on the method
// 405 is returned if it is neither a GET nor a PUT
func syncStatus() http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")

		if r.Method == http.MethodGet {
			getSyncStatus(w, r)
		} else if r.Method == http.MethodPut {
			putSyncStatus(w, r)
		} else {
			w.WriteHeader(http.StatusMethodNotAllowed) // not allowed
		}
	})
}

// getSyncStatus returns the util.Status in JSON form
func getSyncStatus(w http.ResponseWriter, r *http.Request) {
	data, err := json.Marshal(util.Status)
	if err != nil {
		log.Printf("[error] marshaling util.Status: %s\n", err)
		w.WriteHeader(http.StatusInternalServerError)
		return
	}
	w.Header().Set("content-type", "application/json")
	if _, err := io.WriteString(w, string(data)); err != nil {
		log.Printf("[error] %s\n", err)
	}
}

// putSyncStatus updates the util.Status with the input values
// all values are overridden
func putSyncStatus(w http.ResponseWriter, r *http.Request) {
	content, err := ioutil.ReadAll(r.Body)
	if err != nil {
		log.Printf("[error] reading sync status put body: %s\n", err)
		w.WriteHeader(http.StatusInternalServerError)
		return
	}

	if err := json.Unmarshal(content, util.Status); err != nil {
		log.Printf("[error] unmarshaling sync status body: %s: %s\n", content, err)
		w.WriteHeader(http.StatusInternalServerError)
		return
	}

	getSyncStatus(w, r)
}

func sync() http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		timestamp := time.Now().UTC().Unix()

		if r.Method != http.MethodPost {
			log.Printf("[error] sync request failed: only POST or OPTIONS methods are allowed\n")
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}

		decoder := json.NewDecoder(r.Body)
		var params s3.SyncParameters
		err := decoder.Decode(&params)
		if err != nil {
			log.Printf("[error] sync request failed: %s\n", err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}

		go s3.Sync(params)()

		w.Header().Set("content-type", "application/json")

		result := struct {
			Message   string `json:"message"`
			Timestamp int64  `json:"timestamp"`
		}{
			Message:   "Sync command sent",
			Timestamp: timestamp,
		}

		resultBytes, err := json.Marshal(result)
		if err != nil {
			return
		}

		io.WriteString(w, string(resultBytes))
	})
}

func listFiles() http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			log.Printf("[error] list request failed: only GET methods are allowed\n")
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}

		w.Header().Set("content-type", "application/json")
		queryParams := r.URL.Query()
		path := queryParams.Get("path")
		if path == "" {
			w.WriteHeader(http.StatusBadRequest)
			writeJson(w, NewServerError(fmt.Sprintf("Missing query parameter: 'path'")))
			return
		}
		path, err := url.QueryUnescape(path)
		if err != nil {
			w.WriteHeader(http.StatusBadRequest)
			writeJson(w, NewServerError(fmt.Sprintf("Unable to decode 'path'")))
			return
		}

		page := queryParams.Get("page")
		if page == "" {
			page = "1"
		}

		perPage := queryParams.Get("per_page")
		if perPage == "" {
			perPage = "15"
		}

		pageInt, err := strconv.Atoi(page)
		if err != nil {
			w.WriteHeader(http.StatusBadRequest)
			return
		}

		perPageInt, err := strconv.Atoi(perPage)
		if err != nil {
			w.WriteHeader(http.StatusBadRequest)
			return
		}

		options := &file.ListPaginatedFilesOptions{
			Path: path,
			PerPage: perPageInt,
			ShowHidden: false,
			Page: pageInt,
		}
		fileResponse, err := file.ListPaginatedFiles(path, options)
		if err != nil && err == file.PathNotExist {
			fileResponse = &file.PaginatedFileResponse{}
		} else if err != nil && err != file.PathNotExist {
			if err == file.NotADirectory {
				w.WriteHeader(http.StatusBadRequest)
				writeJson(w, NewServerError(fmt.Sprintf("'%v' is not a directory", path)))
			} else {
				w.WriteHeader(http.StatusInternalServerError)
				writeJson(w, NewServerError(err.Error()))
			}

			return
		}

		resultBytes, err := json.Marshal(fileResponse)
		if err != nil {
			return
		}

		if _, err := io.WriteString(w, string(resultBytes)); err != nil {
			log.Printf("error %v", err)
		}
	})
}

func getFileContent() http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			log.Printf("[error] list request failed: only GET methods are allowed\n")
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}

		queryParams := r.URL.Query()
		path := queryParams.Get("path")
		if path == "" {
			w.WriteHeader(http.StatusBadRequest)
			return
		}

		fileInfo, err := os.Stat(path)
		if err != nil {
			w.WriteHeader(http.StatusBadRequest)
			return
		}

		w.Header().Set("Content-Disposition", fmt.Sprintf(`attachment; filename="%v"`, fileInfo.Name()))
		http.ServeFile(w, r, path)
	})
}

func handleUnsupportedEndpoint(config Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		relativeEndpoint := r.URL.Path
		if strings.HasPrefix(r.URL.Path, config.URLPrefix) {
			relativeEndpoint = r.URL.Path[len(config.URLPrefix):]
		}
		log.Printf("Miss [endpoint] %v. Relative: %v", r.URL.Path, relativeEndpoint)
		log.Printf("RequestURI %v. ServerURLPrefix %v", r.URL.Path, config.URLPrefix)

		w.WriteHeader(http.StatusNotFound)
	}
}

// StartServer starts a server that provides information about the file sync status.
func StartServer(config Config) {
	mux := http.NewServeMux()
	chain := alice.New(corsHandler)
	mux.Handle(config.URLPrefix+"/api/status", chain.Then(syncStatus()))
	mux.Handle(config.URLPrefix+"/api/sync", chain.Then(sync()))
	mux.Handle(config.URLPrefix+"/api/files", chain.Then(listFiles()))
	mux.Handle(config.URLPrefix+"/api/files/content", chain.Then(getFileContent()))
	mux.Handle("/", handleUnsupportedEndpoint(config))

	fmt.Printf("Starting server at %s. Prefix: %v\n", config.URL, config.URLPrefix)

	server := &http.Server{Addr: config.URL, Handler: mux}
	go func() {
		if err := server.ListenAndServe(); err != nil {
			if err != http.ErrServerClosed {
				log.Printf("err: %v", err.Error())
			}
		}
	}()

	c := make(chan os.Signal, 1)

	signal.Notify(c, syscall.SIGTERM, os.Interrupt)

	// Block until any signal is received
	s := <-c
	log.Println("Got signal:", s)

	if err := server.Shutdown(context.Background()); err != nil {
		log.Printf("error shutting down: %v", err.Error())
 	} else {
		log.Printf("Shut down server")
	}
}
