package main

import "fmt"

func main() {
	for i := 999; i < len(RandomString); i += 1000 {
		fmt.Printf("Character at position %d: %c\n", i+1, RandomString[i])
	}
}