package trigger

import (
	"errors"
	"fmt"
	"os/exec"
)

type OpenFaaSTrigger struct {
	Funtions map[string]string
}

func new() *OpenFaaSTrigger {
	return &OpenFaaSTrigger{
		Funtions: map[string]string{
			"mnist-preprocess": "openfaas/functions/mnist-preprocess.yml",
			"mnist-training-model": "openfaas/functions/mnist-training-model.yml",
			"mnist-model-evaluate": "openfaas/functions/mnist-model-evaluate.yml",
		},
	}
}

var ErrNotFoundFunction = errors.New("OpenFaaS Function not found")

func (oft *OpenFaaSTrigger) GetFunction(name string) (deployYamlFile string, err error) {
	deployYamlFile, exists := oft.Funtions[name]
	if !exists {
		return "", ErrNotFoundFunction
	}
	return deployYamlFile, nil
}

func (oft *OpenFaaSTrigger) GetAllFunctions() map[string]string {
	return oft.Funtions
}

func (oft *OpenFaaSTrigger) Deploy(yamlFile string) error {
	cmd := exec.Command("faas-cli", "deploy", "-f", yamlFile)
	output, err := cmd.Output()
	if err != nil {
		fmt.Println("Deploy Error: ", err.Error())
		return err
	}
	fmt.Println("Deployed Result: ", string(output))
	return nil
}

func (oft *OpenFaaSTrigger) Remove(yamlFile string) error {
	cmd := exec.Command("faas-cli", "remove", "-f", yamlFile)
	output, err := cmd.Output()
	if err != nil {
		fmt.Println("Remove Error: ", err.Error())
		return err
	}
	fmt.Println("Removed Result: ", string(output))
	return nil
}

func (oft *OpenFaaSTrigger) Invoke(
	method string,
	openfaasGateway string, 
	functionName string,
) error {
	return request(method, openfaasGateway, functionName)
}