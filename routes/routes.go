package routes

import (
	"fmt"

	"github.com/gin-gonic/gin"
	"leoho.io/mnist-openfaas-trigger/trigger"
)

var host = getLocalNetworkIPv4Address().String()
const port = "8000"

func SetupRoute() {
	app := gin.Default()

	app.POST("/function/mnist-faas-trigger", trigger.TriggerHandler)

	app.Run(fmt.Sprintf("%s:%s", host, port))
}