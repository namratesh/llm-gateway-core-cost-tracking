# pricing.py

# Simulated pricing per 1,000,000 tokens (similar to Groq/OpenAI pricing)
PRICING_TABLE = {
    "qwen3:4b": {"input": 0.10, "output": 0.10},  # Cheap
    "deepseek-r1:8b":      {"input": 0.50, "output": 1.50},  # Standard
    "default":     {"input": 0.50, "output": 1.50}
}

def estimate_tokens(text: str) -> int:
    """
    Fast heuristic: ~4 chars per token.
    For production, use 'tiktoken' or similar libraries.
    """
    if not text:
        return 0
    return len(text) // 4

def calculate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """
    Returns estimated cost in USD.
    """
    model_price = PRICING_TABLE.get(model_name, PRICING_TABLE["default"])
    
    input_cost = (input_tokens / 1_000_000) * model_price["input"]
    output_cost = (output_tokens / 1_000_000) * model_price["output"]
    
    return round(input_cost + output_cost, 8)