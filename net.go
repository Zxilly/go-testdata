package main

import (
	"io"
	"net/http"
	"strconv"
)

//go:noline
func UsingNet() {
	resp, err := http.Get("https://www.baidu.com")
	if err != nil {
		panic(err)
	}
	content, err := io.ReadAll(resp.Body)
	if err != nil {
		panic(nil)
	}

	println("resp size:" + strconv.Itoa(len(content)))
}
