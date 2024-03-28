package apis

type TriggerRequest struct {
	// CurrentStage is the current stage function name
	CurrentStage string `json:"current_stage"`

	// NextStage is the next stage function name
	NextStage string `json:"next_stage"`
}