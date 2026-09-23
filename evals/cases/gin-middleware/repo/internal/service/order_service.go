package service

import "log"

func CreateOrder(name string) error {
	log.Printf("creating order for %s", name)
	return nil
}
