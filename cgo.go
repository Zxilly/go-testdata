//go:build cgo
// +build cgo

package main

/*
#include <stdio.h>

int printint(int v) {
	return v * 123456;
}
*/
import "C"
import "fmt"

func init() {
	v := 42
	fmt.Println(C.printint(C.int(v)))
}
