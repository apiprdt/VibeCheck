package main

import (
	"fmt"
	"sync"
)

var counter int
var wg sync.WaitGroup

func increment() {
	defer wg.Done()
	counter++
}

func main() {
	for i := 0; i < 1000; i++ {
		wg.Add(1)
		go increment()
	}
	wg.Wait()
	fmt.Println(counter)
}
