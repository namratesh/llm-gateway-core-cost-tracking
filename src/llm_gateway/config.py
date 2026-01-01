from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Callable

class ModelPricing(BaseModel):
    input_cost_per_m: float
    output_cost_per_m: float

class RoutingRule(BaseModel):
    max_tokens: int
    keywords: List[str]
    target_model: str

class GatewayConfig(BaseModel):
    # Default pricing if a specific model isn't found
    default_pricing: ModelPricing = ModelPricing(input_cost_per_m=0.50, output_cost_per_m=1.50)
    
    # Map model names to pricing
    pricing_table: Dict[str, ModelPricing] = {}
    
    # Routing heuristics
    routing_rules: List[RoutingRule] = []
    
    # Fallback model if routing fails
    fallback_model: str = "llama3"
    
    # Logging configuration (path to file)
    log_path: str = "gateway_logs.jsonl"