import time
import uuid
import logging
import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from .config import GatewayConfig
from .utils import estimate_tokens, calculate_cost_from_config, append_log

logger = logging.getLogger("LLM-Gateway")

class LLMCostMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, config: GatewayConfig):
        super().__init__(app)
        self.config = config  # Store the user's config

    async def dispatch(self, request: Request, call_next):
        # 1. Setup
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # 2. Body Capture (Standard Safe Re-wrapping)
        body_bytes = await request.body()
        async def receive():
            return {"type": "http.request", "body": body_bytes}
        request._receive = receive

        # 3. Routing Logic (Using self.config)
        try:
            body_json = json.loads(body_bytes)
            prompt = body_json.get("prompt", "")
            
            # Simple router loop based on config rules
            selected_model = self.config.fallback_model
            complexity_score = 0
            
            # Estimate tokens for routing
            input_len = len(prompt) // 4
            
            for rule in self.config.routing_rules:
                # Check keyword matches
                if any(k in prompt.lower() for k in rule.keywords):
                    selected_model = rule.target_model
                    complexity_score = 10
                    break
                # Check length constraints
                if input_len > rule.max_tokens:
                    selected_model = rule.target_model
                    complexity_score = 5
            
        except:
            prompt = ""
            selected_model = self.config.fallback_model
            complexity_score = 0

        # Inject into State
        request.state.request_id = request_id
        request.state.target_model = selected_model

        # 4. Call Application
        response = await call_next(request)

        # 5. Capture Response & Log
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        
        new_response = Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )
        
        # Calculate Costs using Config
        process_time = (time.time() - start_time) * 1000
        
        # (Simplified decoding for brevity)
        try:
            resp_json = json.loads(response_body)
            output_text = resp_json.get("response", "")
        except:
            output_text = ""

        input_tokens = estimate_tokens(prompt)
        output_tokens = estimate_tokens(output_text)
        
        # Use the config to find the price
        cost = calculate_cost_from_config(self.config, selected_model, input_tokens, output_tokens)
        
        # Write Log
        append_log(self.config.log_path, {
            "req_id": request_id,
            "model": selected_model,
            "cost": cost,
            "latency": process_time
        })
        
        return new_response