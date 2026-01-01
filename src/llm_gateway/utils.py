# src/llm_gateway/utils.py
import json
import os
from datetime import datetime

def estimate_tokens(text: str) -> int:
    """
    Fast heuristic: ~4 chars per token.
    """
    if not text:
        return 0
    return len(text) // 4

def calculate_cost_from_config(config, model_name: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculates cost based on the user's provided configuration object.
    """
    # Try to find specific pricing for this model, otherwise use default
    price_model = config.pricing_table.get(model_name, config.default_pricing)
    
    input_cost = (input_tokens / 1_000_000) * price_model.input_cost_per_m
    output_cost = (output_tokens / 1_000_000) * price_model.output_cost_per_m
    
    return round(input_cost + output_cost, 8)

def append_log(log_path: str, log_entry: dict):
    """
    Appends a log entry to the specified JSONL file.
    """
    # Add timestamp if missing
    if "timestamp" not in log_entry:
        log_entry["timestamp"] = datetime.utcnow().isoformat()
        
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        # In prod, you might use standard logging here instead of print
        print(f"LLM-GATEWAY LOGGING ERROR: {e}")