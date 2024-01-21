//go:build go1.16
// +build go1.16

package main

import _ "embed"

//go:embed LICENSE
var LICENSE string

//go:noline
func UsingEmbed() {
	println(LICENSE)
}
