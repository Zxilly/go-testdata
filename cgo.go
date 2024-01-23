//go:build with_cgo
// +build with_cgo

package main

/*
#include <stdio.h>

void printint(int v) {
    printf("Print from cgo:", v);
}
*/
import "C"

func init() {
	C.printint(C.int(42))
}
