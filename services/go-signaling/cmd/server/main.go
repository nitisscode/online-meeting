package main

import (
	"log"
	"net/http"
	"os"
)

func main() {
	port := os.Getenv("GO_SIGNALING_PORT")
	if port == "" {
		port = "8080"
	}

	http.HandleFunc("/health", func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("ok"))
	})

	log.Printf("go-signaling scaffold listening on :%s", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
