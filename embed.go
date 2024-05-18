//go:build go1.16
// +build go1.16

package main

import "embed"

//go:embed LICENSE
var licenseBytes []byte

//go:embed README.md
var readme string

//go:embed *.go
var goFiles embed.FS

//go:noinline
func UsingEmbedBytes() {
	println(string(licenseBytes))
}

//go:noinline
func UsingEmbedString() {
	println(readme)
}

//go:noinline
func UsingEmbedFS() {
	files, _ := goFiles.ReadDir(".")
	for _, file := range files {
		println(file.Name())
	}
}

func init() {
	UsingEmbedBytes()
	UsingEmbedString()
	UsingEmbedFS()
}
