//go:build main1
// +build main1

package main

import "embed"

//go:embed LICENSE
var licenseBytes []byte

//go:embed README.md
var readme string

//go:embed *.go
var goFiles embed.FS

func init() {
	println(string(licenseBytes))
	println(readme)
	files, _ := goFiles.ReadDir(".")
	for _, file := range files {
		println(file.Name())
	}
}
