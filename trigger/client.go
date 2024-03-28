package trigger

import (
	"fmt"
	"net/http"
)

func request(
	method string,
	openfaasGateway string,
	functionName string,
) error {
	url := fmt.Sprintf("http://%s/function/%s", openfaasGateway, functionName)
	req, err := http.NewRequest(method, url, nil)
	if err != nil {
		return err
	}
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	return nil
}