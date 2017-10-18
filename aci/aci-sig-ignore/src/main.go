package main

//#include <unistd.h>
import "C"

import (
	"fmt"
	"os"
	"os/signal"
	"syscall"
)

var ignoreSIG = []os.Signal{syscall.SIGINT, syscall.SIGTERM}

func main() {
	C.fork()
	for _, s := range ignoreSIG {
		println(fmt.Sprintf("pid %d ignoring %q", os.Getpid(), s.String()))
		signal.Ignore(s)
	}
	ch := make(chan struct{})
	<-ch
	return
}
