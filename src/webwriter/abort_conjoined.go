package main

import (
	"log"
	"net/http"
)

func abortConjoined(responseWriter http.ResponseWriter,
	request *http.Request, parsedRequest ParsedRequest) {

	log.Printf("debug: %s; %s %s %s %d", parsedRequest.Type,
		parsedRequest.RequestID, parsedRequest.CollectionName,
		parsedRequest.Key, parsedRequest.UnifiedID)

	http.Error(responseWriter, "Not implemented",
		http.StatusInternalServerError)
}