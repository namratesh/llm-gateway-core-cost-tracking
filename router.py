import re
# Define your available models here
MODEL_SMALL = "qwen3:4b"  
MODEL_LARGE = "deepseek-r1:8b"     #

def get_complexity_score(prompt: str) -> dict:
    """
    Analyzes prompt to determine complexity.
    Returns a dictionary with score details and selected model.
    """
    score = 0
    reasons = []
    
    # 1. Length Heuristic
    # Short queries are usually factual or greetings
    if len(prompt) < 200:
        score += 1
        reasons.append("short_input")
    else:
        score += 5
        reasons.append("long_input")

    # 2. Keyword Heuristic (Reasoning/Coding indicators)
    # These imply the user wants 'intelligence' not just retrieval
    complex_keywords = ["explain", "why", "code", "function", "analyze", "compare", "step-by-step"]
    if any(word in prompt.lower() for word in complex_keywords):
        score += 10
        reasons.append("complex_intent")

    # 3. Decision Logic
    # Threshold: If score > 5, use the smart model. Else, use the fast model.
    if score > 5:
        selected_model = MODEL_LARGE
    else:
        selected_model = MODEL_SMALL

    return {
        "score": score,
        "reasons": reasons,
        "model": selected_model
    }