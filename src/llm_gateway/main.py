from fastapi import FastAPI, Request
from llm_gateway import LLMCostMiddleware, GatewayConfig, ModelPricing, RoutingRule

app = FastAPI()

# 1. Define MY specific rules
my_config = GatewayConfig(
    fallback_model="llama3",
    pricing_table={
        "qwen3:4b": ModelPricing(input_cost_per_m=0.1, output_cost_per_m=0.1),
        "deepseek-r1:8b":      ModelPricing(input_cost_per_m=0.5, output_cost_per_m=1.5),
    },

    routing_rules=[
        # Route cheap queries to mini
        RoutingRule(max_tokens=200, keywords=[], target_model="llama3-mini"),
        # Route reasoning to standard
        RoutingRule(max_tokens=9999, keywords=["explain", "why"], target_model="llama3"),
    ]
)

# 2. Add the Middleware with ONE line
app.add_middleware(LLMCostMiddleware, config=my_config)

# 3. My normal endpoint (The middleware handles the heavy lifting)
@app.post("/generate")
async def generate(request: Request):
    # The middleware already decided the model!
    model_to_use = request.state.target_model
    return {"status": "success", "model_used": model_to_use}