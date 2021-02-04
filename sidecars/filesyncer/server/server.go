package server

import (
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"strings"
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
		start := time.Now().UTC().Unix()

		if r.Method != http.MethodPost {
			log.Printf("[error] sync request failed: only POST or OPTIONS methods are allowed allowed\n")
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
			Message string `json:"message"`
			Start int64 `json:"start"`
		} {
			Message: "Sync command sent",
			Start: start,
		}

		resultBytes, err := json.Marshal(result)
		if err != nil {
			return
		}

		io.WriteString(w, string(resultBytes))
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
	mux.Handle("/", handleUnsupportedEndpoint(config))

	fmt.Printf("Starting server at %s. Prefix: %v\n", config.URL, config.URLPrefix)
	err := http.ListenAndServe(config.URL, mux)
	log.Printf("%v", err)
}
