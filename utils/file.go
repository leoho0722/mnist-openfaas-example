package utils

import (
	"errors"
	"fmt"
	"log"
	"os"
)

func FileExists(path string) (bool, error) {
	file, err := os.Open(path)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			log.Fatalf("%s not exist\n", path)
			return false, err
		}
		log.Fatalf("Open file error: %v\n", err)
		return false, err
	}
	defer func(file *os.File) {
		err := file.Close()
		if err != nil {
			log.Fatalf("Close file error: %v\n", err)
			panic(err)
		}
	}(file)

	fmt.Printf("%s exist\n", path)

	return true, nil
}