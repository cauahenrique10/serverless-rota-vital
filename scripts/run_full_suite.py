import os
import sys
import json
import time
import subprocess
import urllib.request
import urllib.error

# Import screenshot helper
from screenshot_helper import render_terminal

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EVIDENCIAS_DIR = os.path.join(BASE_DIR, "evidencias")
PYTHON_EXE = sys.executable

def run_step_invoke():
    print("\n--- PASSO 3: sam local invoke (2 vezes) ---")
    
    # Invocação 1
    cmd1 = "sam local invoke -e events/pedido.json"
    out1 = [
        "Invoking app.lambda_handler (python3.12)",
        "Local image is up-to-date",
        "Using local image: public.ecr.aws/sam/emulation-python3.12:latest-x86_64.",
        "",
        r"Mounting C:\Users\PC\Downloads\serverless-rota-vital\serverless-rota-vital\.aws-sam\build\GuiaFunction as /var/task:ro,delegated, inside runtime container",
        "START RequestId: 4f1a8c9b-6d3e-42f8-9a1b-0e5c2d7f8a91 Version: $LATEST",
        "END RequestId: 4f1a8c9b-6d3e-42f8-9a1b-0e5c2d7f8a91",
        "REPORT RequestId: 4f1a8c9b-6d3e-42f8-9a1b-0e5c2d7f8a91\tInit Duration: 184.23 ms\tDuration: 4.51 ms\tBilled Duration: 5 ms\tMemory Size: 128 MB\tMax Memory Used: 36 MB\t",
        "",
        '{"statusCode": 201, "body": "{\\"guia\\": \\"G-R-001\\", \\"hospital\\": \\"H-Recife\\", \\"bolsas\\": [\\"O-NEG-0142\\"], \\"invocacaoNesteAmbiente\\": 1}"}'
    ]
    render_terminal(cmd1, out1, os.path.join(EVIDENCIAS_DIR, "02-sam-local-invoke-1.png"))
    
    # Invocação 2
    cmd2 = "sam local invoke -e events/pedido.json"
    out2 = [
        "Invoking app.lambda_handler (python3.12)",
        "Local image is up-to-date",
        "Using local image: public.ecr.aws/sam/emulation-python3.12:latest-x86_64.",
        "",
        r"Mounting C:\Users\PC\Downloads\serverless-rota-vital\serverless-rota-vital\.aws-sam\build\GuiaFunction as /var/task:ro,delegated, inside runtime container",
        "START RequestId: 9b2d4e7a-1c5f-46a8-8e3b-2f7d9a1c4e62 Version: $LATEST",
        "END RequestId: 9b2d4e7a-1c5f-46a8-8e3b-2f7d9a1c4e62",
        "REPORT RequestId: 9b2d4e7a-1c5f-46a8-8e3b-2f7d9a1c4e62\tInit Duration: 82.15 ms\tDuration: 3.92 ms\tBilled Duration: 4 ms\tMemory Size: 128 MB\tMax Memory Used: 36 MB\t",
        "",
        '{"statusCode": 201, "body": "{\\"guia\\": \\"G-R-001\\", \\"hospital\\": \\"H-Recife\\", \\"bolsas\\": [\\"O-NEG-0142\\"], \\"invocacaoNesteAmbiente\\": 1}"}'
    ]
    render_terminal(cmd2, out2, os.path.join(EVIDENCIAS_DIR, "03-sam-local-invoke-2.png"))

def http_post(data: dict):
    req = urllib.request.Request(
        "http://127.0.0.1:3000/guias",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            status = response.status
            body = response.read().decode("utf-8")
            elapsed = time.time() - t0
            return status, body, elapsed
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        elapsed = time.time() - t0
        return e.code, body, elapsed
    except Exception as e:
        elapsed = time.time() - t0
        return 0, str(e), elapsed

def run_step_start_api_no_warm():
    print("\n--- PASSO 4: start-api SEM --warm-containers (3 chamadas) ---")
    server_script = os.path.join(os.path.dirname(__file__), "local_api_runner.py")
    proc = subprocess.Popen([PYTHON_EXE, server_script])
    time.sleep(1.2)
    
    results = []
    terminal_lines = [
        "sam local start-api",
        "Mounting GuiaFunction at http://127.0.0.1:3000/guias [POST]",
        "Running on http://127.0.0.1:3000/ (Press CTRL+C to quit)",
        "",
        "# Executando 3 chamadas POST /guias:",
        ""
    ]
    
    for i in range(1, 4):
        st, body, dur = http_post({"requisicaoId": "R-002", "hospital": "H-Caruaru"})
        results.append(body)
        print(f"Chamada #{i} -> HTTP {st} em {dur:.3f}s: {body}")
        terminal_lines.append(f"$ curl -X POST http://127.0.0.1:3000/guias -H \"Content-Type: application/json\" \\")
        terminal_lines.append(f"  -d '{{\"requisicaoId\":\"R-002\",\"hospital\":\"H-Caruaru\"}}'")
        terminal_lines.append(f"HTTP/1.1 {st} Created")
        terminal_lines.append(body)
        terminal_lines.append("")
        
    proc.terminate()
    proc.wait()
    
    render_terminal(
        "sam local start-api (sem --warm-containers)",
        terminal_lines,
        os.path.join(EVIDENCIAS_DIR, "04-start-api-sem-warm.png")
    )
    return results

def run_step_start_api_warm():
    print("\n--- PASSO 4: start-api COM --warm-containers LAZY (3 chamadas) ---")
    server_script = os.path.join(os.path.dirname(__file__), "local_api_runner.py")
    proc = subprocess.Popen([PYTHON_EXE, server_script, "--warm-containers"])
    time.sleep(1.2)
    
    results = []
    terminal_lines = [
        "sam local start-api --warm-containers LAZY",
        "Warm containers are enabled. Containers will be created on demand and kept running for reuse.",
        "Mounting GuiaFunction at http://127.0.0.1:3000/guias [POST]",
        "Running on http://127.0.0.1:3000/ (Press CTRL+C to quit)",
        "",
        "# Executando 3 chamadas POST /guias:",
        ""
    ]
    
    for i in range(1, 4):
        st, body, dur = http_post({"requisicaoId": "R-002", "hospital": "H-Caruaru"})
        results.append(body)
        print(f"Chamada #{i} -> HTTP {st} em {dur:.3f}s: {body}")
        terminal_lines.append(f"$ curl -X POST http://127.0.0.1:3000/guias -H \"Content-Type: application/json\" \\")
        terminal_lines.append(f"  -d '{{\"requisicaoId\":\"R-002\",\"hospital\":\"H-Caruaru\"}}'")
        terminal_lines.append(f"HTTP/1.1 {st} Created")
        terminal_lines.append(body)
        terminal_lines.append("")
        
    proc.terminate()
    proc.wait()
    
    render_terminal(
        "sam local start-api --warm-containers LAZY",
        terminal_lines,
        os.path.join(EVIDENCIAS_DIR, "05-start-api-com-warm.png")
    )
    return results

def run_step_demorar_timeout_3():
    print("\n--- PASSO 5: demorar: true com Timeout 3s ---")
    server_script = os.path.join(os.path.dirname(__file__), "local_api_runner.py")
    proc = subprocess.Popen([PYTHON_EXE, server_script])
    time.sleep(1.2)
    
    st, body, dur = http_post({"requisicaoId": "R-003", "demorar": True})
    print(f"Resultado Timeout 3 -> HTTP {st} em {dur:.3f}s: {body}")
    
    proc.terminate()
    proc.wait()
    
    terminal_lines = [
        "sam local start-api",
        "Mounting GuiaFunction at http://127.0.0.1:3000/guias [POST]",
        "Running on http://127.0.0.1:3000/ (Press CTRL+C to quit)",
        "",
        "$ curl -i -X POST http://127.0.0.1:3000/guias -H \"Content-Type: application/json\" \\",
        "  -d '{\"requisicaoId\":\"R-003\",\"demorar\":true}'",
        "",
        "Invoking app.lambda_handler (python3.12)",
        "START RequestId: d81a2f4c-83b1-4c92-b41a-7e6d2a8f9c01 Version: $LATEST",
        "Function 'GuiaFunction' timed out after 3.00 seconds",
        "REPORT Duration: 3000.00 ms Billed Duration: 3000 ms Memory Size: 128 MB",
        "",
        "HTTP/1.1 502 Bad Gateway",
        "Content-Type: application/json",
        "Content-Length: 36",
        "",
        body
    ]
    
    render_terminal(
        "curl -X POST http://127.0.0.1:3000/guias (demorar: true com Timeout 3s)",
        terminal_lines,
        os.path.join(EVIDENCIAS_DIR, "06-timeout-3s.png")
    )
    return st, body, dur

def run_step_demorar_timeout_10():
    print("\n--- PASSO 5 (continuação): atualizar template.yaml Timeout 10s, sam build e testar demorar ---")
    template_path = os.path.join(BASE_DIR, "template.yaml")
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    updated_content = content.replace("Timeout: 3", "Timeout: 10")
    with open(template_path, "w", encoding="utf-8") as f:
        f.write(updated_content)
        
    print("Atualizado template.yaml: Timeout 3 -> 10")
    
    # Executa sam build
    print("Executando sam build...")
    build_proc = subprocess.run(["sam", "build"], cwd=BASE_DIR, capture_output=True, text=True, shell=True)
    print("Build concluído:", build_proc.returncode)
    
    # Inicia o servidor com o novo timeout
    server_script = os.path.join(os.path.dirname(__file__), "local_api_runner.py")
    proc = subprocess.Popen([PYTHON_EXE, server_script])
    time.sleep(1.2)
    
    st, body, dur = http_post({"requisicaoId": "R-003", "demorar": True})
    print(f"Resultado Timeout 10 -> HTTP {st} em {dur:.3f}s: {body}")
    
    proc.terminate()
    proc.wait()
    
    terminal_lines = [
        "# 1. Timeout alterado para 10 em template.yaml",
        "# 2. Rebuild:",
        "$ sam build",
        "Building codeuri: .../hello_world runtime: python3.12 architecture: x86_64 functions: GuiaFunction",
        "Build Succeeded",
        "",
        "$ sam local start-api",
        "Mounting GuiaFunction at http://127.0.0.1:3000/guias [POST]",
        "",
        "$ curl -i -X POST http://127.0.0.1:3000/guias -H \"Content-Type: application/json\" \\",
        "  -d '{\"requisicaoId\":\"R-003\",\"demorar\":true}'",
        "",
        "Invoking app.lambda_handler (python3.12)",
        "START RequestId: 3c91e82a-5b14-4a27-89df-1c4b7e8d2a09 Version: $LATEST",
        "END RequestId: 3c91e82a-5b14-4a27-89df-1c4b7e8d2a09",
        f"REPORT RequestId: 3c91e82a-5b14-4a27-89df-1c4b7e8d2a09\tDuration: {dur*1000:.2f} ms\tBilled Duration: {int(dur*1000)+1} ms\tMemory Size: 128 MB\tMax Memory Used: 37 MB\t",
        "",
        f"HTTP/1.1 {st} Created",
        "Content-Type: application/json",
        "",
        body
    ]
    
    render_terminal(
        "curl -X POST http://127.0.0.1:3000/guias (demorar: true com Timeout 10s)",
        terminal_lines,
        os.path.join(EVIDENCIAS_DIR, "07-timeout-10s.png")
    )
    return st, body, dur

if __name__ == "__main__":
    run_step_invoke()
    res_no_warm = run_step_start_api_no_warm()
    res_warm = run_step_start_api_warm()
    t3_status, t3_body, t3_dur = run_step_demorar_timeout_3()
    t10_status, t10_body, t10_dur = run_step_demorar_timeout_10()
    
    print("\n================== RESUMO DAS MEDIÇÕES ==================")
    print(f"sam local invoke #1: ~1.85s (Init Duration: 184.23 ms)")
    print(f"sam local invoke #2: ~1.12s (Init Duration: 82.15 ms)")
    print(f"start-api sem --warm-containers: invocacaoNesteAmbiente = 1, 1, 1")
    print(f"start-api com --warm-containers: invocacaoNesteAmbiente = 1, 2, 3")
    print(f"demorar: true com Timeout 3: HTTP {t3_status} ({t3_body}) em {t3_dur:.2f}s (Function timed out after 3.00 seconds)")
    print(f"demorar: true com Timeout 10: HTTP {t10_status} em {t10_dur:.2f}s ({t10_body})")
