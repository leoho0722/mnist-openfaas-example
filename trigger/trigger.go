package trigger

import (
	"fmt"

	"leoho.io/mnist-openfaas-trigger/apis"
	"leoho.io/mnist-openfaas-trigger/utils"

	"github.com/gin-gonic/gin"
)

func TriggerHandler(c *gin.Context) {
	// Parse the request
	var data *apis.TriggerRequest
	err := c.BindJSON(&data)
	if err != nil {
		c.JSON(
			400, 
			apis.ErrorResponse{
				Error: "Invalid request",
			},
		)
		return
	}

	openfaasTrigger := new()

	// Check if the next stage function exists
	nextStageDeployYamlFile, err := openfaasTrigger.GetFunction(data.NextStage)
	if err != nil {
		c.JSON(
			404,
			apis.ErrorResponse{
				Error: fmt.Sprintf("Next stage Funtion %s not found", data.NextStage),
			},
		)
		return
	}
	// Check if the next stage function deploy file exists
	isExist, err := utils.FileExists(nextStageDeployYamlFile)
	if err != nil || !isExist {
		c.JSON(
			500,
			apis.ErrorResponse{
				Error: "Next stage Function deploy file does not exist.",
			},
		)
		return
	}
	// Deploy the next stage function
	err = openfaasTrigger.Deploy(nextStageDeployYamlFile)
	if err != nil {
		c.JSON(
			500,
			apis.ErrorResponse{
				Error: "Failed to deploy next stage Function.",
			},
		)
		return
	}

	// Invoke the next stage function
	err = openfaasTrigger.Invoke("GET", "127.0.0.1:8080", data.NextStage)
	if err != nil {
		c.JSON(
			500,
			apis.ErrorResponse{
				Error: "Failed to invoke next stage Function.",
			},
		)
		return
	}

	if data.CurrentStage != "" {
		// Remove the last stage function
		lastStageDeployYamlFile, err := openfaasTrigger.GetFunction(data.CurrentStage)
		if err != nil {
			c.JSON(
				404,
				apis.ErrorResponse{
					Error: fmt.Sprintf("Last stage Funtion %s not found", data.CurrentStage),
				},
			)
			return
		}
		// Check if the last stage function deploy file exists
		isExist, err = utils.FileExists(lastStageDeployYamlFile)
		if err != nil || !isExist {
			c.JSON(
				500,
				apis.ErrorResponse{
					Error: "Last stage Function deploy file does not exist.",
				},
			)
			return
		}
		// Remove the last stage function
		err = openfaasTrigger.Remove(lastStageDeployYamlFile)
		if err != nil {
			c.JSON(
				500,
				apis.ErrorResponse{
					Error: "Failed to remove last stage Function.",
				},
			)
			return
		}
	}

	c.JSON(
		200,
		apis.GeneralResponse{
			Message: fmt.Sprintf("Triggered %s and removed %s", data.NextStage, data.CurrentStage),
		},
	)
}