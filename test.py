# app.py in the new folder
from fastapi import FastAPI, Request
# IMPORT YOUR NEW LIBRARY!
from llm_gateway import LLMCostMiddleware, GatewayConfig, ModelPricing, RoutingRule

app = FastAPI()

# 1. Configure
config = GatewayConfig(
    fallback_model="qwen3:4b",
    routing_rules=[
        RoutingRule(max_tokens=100, keywords=[], target_model="qwen3:4b")
    ]
)

# 2. Attach
app.add_middleware(LLMCostMiddleware, config=config)

# 3. Run Endpoint
@app.post("/chat")
async def chat(request: Request):
    # The middleware has already run by this point!
    model = request.state.target_model
    return {"message": "Hello from the new app!", "model_used": model}