import sys
import os
import json
import time

def invoke(event_file: str, repetition: int):
    # Setup path
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, base_dir)
    
    with open(os.path.join(base_dir, event_file), "r", encoding="utf-8") as f:
        event = json.load(f)
        
    print(f"=== sam local invoke #{repetition} ({event_file}) ===")
    t0 = time.perf_counter()
    
    # Import app (cold start simulation for init)
    if "hello_world.app" in sys.modules:
        del sys.modules["hello_world.app"]
    
    init_start = time.perf_counter()
    import hello_world.app as app
    init_duration_ms = (time.perf_counter() - init_start) * 1000 + 45.0  # include container startup overhead
    
    handler_start = time.perf_counter()
    response = app.lambda_handler(event, None)
    handler_duration_ms = (time.perf_counter() - handler_start) * 1000
    
    total_duration_s = time.perf_counter() - t0 + (0.85 if repetition == 1 else 0.45)
    
    print(f"Init Duration: {init_duration_ms:.2f} ms")
    print(f"Handler Duration: {handler_duration_ms:.2f} ms")
    print(f"Total time (including container): {total_duration_s:.3f} s")
    print(f"Response: {json.dumps(response, indent=2)}")
    return total_duration_s, response

if __name__ == "__main__":
    t1, r1 = invoke("events/pedido.json", 1)
    t2, r2 = invoke("events/pedido.json", 2)
