//go:build cgo
// +build cgo

package main

/*
#include <stdio.h>

void printint(int v) {
	printf("printint: %d\n", v);
}
*/
import "C"

func init() {
	v := 42
	C.printint(C.int(v))
}
