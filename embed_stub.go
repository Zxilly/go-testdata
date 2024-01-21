//go:build !go1.16
// +build !go1.16

package main

const LICENSE = "A LICENSE String"

//go:noline
func UsingEmbed() {
	println(LICENSE)
}
