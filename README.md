# LLM Gateway Core

A robust, production-ready FastAPI middleware for LLM applications. It acts as an intelligent layer that routes requests, tracks costs, and logs usage metrics before they reach your LLM inference engine.

## Features

- **💰 Cost Tracking**: Estimates token usage and tracks costs based on configurable pricing models (per million tokens).
- **🔀 Intelligent Routing**: Dynamically directs requests to different models (e.g., "fast" vs "smart") based on prompt complexity and keywords.
- **📊 Observability**: Logs detailed metrics (latency, model used, cost) to a JSONL file.
- **🔌 Easy Integration**: Designed as a drop-in `FastAPI` middleware.

## Installation

```bash
pip install llm-gateway-core
```

*For local development:*
```bash
pip install -e .
```

## Usage

Here is an example of how to attach the middleware to your FastAPI application:

```python
from fastapi import FastAPI, Request
from llm_gateway import LLMCostMiddleware, GatewayConfig, ModelPricing, RoutingRule

app = FastAPI()

# 1. Define Configuration
config = GatewayConfig(
    # Default model to use if no rules match
    fallback_model="qwen3:4b", 
    
    # Define pricing for specific models (USD per 1M tokens)
    pricing_table={
        "qwen3:4b": ModelPricing(input_cost_per_m=0.10, output_cost_per_m=0.20),
        "deepseek-r1": ModelPricing(input_cost_per_m=2.50, output_cost_per_m=10.00),
    },
    
    # Define Routing Rules
    routing_rules=[
        # Use a stronger model for complex keywords
        RoutingRule(
            max_tokens=9999, 
            keywords=["analyze", "reason", "complex"], 
            target_model="deepseek-r1"
        ),
        # Use a specific model for long contexts
        RoutingRule(
            max_tokens=1000, 
            keywords=[], 
            target_model="qwen3:4b"  # Example: switch to cheaper model for bulk text
        )
    ],
    
    # Path to save logs
    log_path="gateway_logs.jsonl"
)

# 2. Add Middleware
app.add_middleware(LLMCostMiddleware, config=config)

# 3. Access Routing Decisions in Endpoints
@app.post("/chat")
async def chat(request: Request):
    # The middleware injects the selected model into `request.state`
    selected_model = request.state.target_model
    request_id = request.state.request_id
    
    # Your logic here (e.g., call Ollama with selected_model)
    return {
        "message": f"Processed using {selected_model}", 
        "request_id": request_id
    }
```

## Configuration

### `GatewayConfig`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `fallback_model` | `str` | `"llama3"` | Model to use when no routing rules match. |
| `log_path` | `str` | `"gateway_logs.jsonl"` | Path to the JSONL log file. |
| `routing_rules` | `List[RoutingRule]` | `[]` | List of rules to determine model selection. |
| `pricing_table` | `Dict[str, ModelPricing]` | `{}` | Cost configuration for each model. |
| `default_pricing` | `ModelPricing` | `$0.50` in/out | Pricing used if model is not in the table. |

### `RoutingRule`

| Field | Type | Description |
|-------|------|-------------|
| `keywords` | `List[str]` | If prompt contains any of these, this rule matches. |
| `max_tokens` | `int` | Length threshold. If prompt length > match, this rule triggers. |
| `target_model` | `str` | The model ID to assign (e.g., `gpt-4`, `llama3`). |
