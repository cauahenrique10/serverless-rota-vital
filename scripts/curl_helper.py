import sys
import os
import json
import re
import urllib.request
import urllib.error

def clean_powershell_json(s: str) -> str:
    s = s.strip()
    
    # Try parsing directly
    try:
        json.loads(s)
        return s
    except:
        pass
        
    # Remove all stray backslashes introduced by PowerShell escaping
    s = s.replace("\\", "")
    
    # Format keys with double quotes
    s = re.sub(r'([a-zA-Z0-9_]+)\s*:', r'"\1":', s)
    
    # Format string values with double quotes (skip booleans and numbers)
    def repl_val(m):
        val = m.group(1).strip()
        if val in ("true", "false", "null") or val.isdigit():
            return f': {val}'
        if val.startswith('"') and val.endswith('"'):
            return f': {val}'
        return f': "{val}"'
        
    s = re.sub(r':\s*([a-zA-Z0-9_\-]+)', repl_val, s)
    return s

def main():
    args = sys.argv[1:]
    
    url = "http://127.0.0.1:3000/guias"
    method = "POST"
    data = None
    headers = {"Content-Type": "application/json"}
    
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("-X", "--request") and i + 1 < len(args):
            method = args[i + 1]
            i += 2
        elif arg in ("-H", "--header") and i + 1 < len(args):
            h = args[i + 1]
            if ":" in h:
                k, v = h.split(":", 1)
                headers[k.strip()] = v.strip()
            i += 2
        elif arg in ("-d", "--data", "--data-raw") and i + 1 < len(args):
            data = args[i + 1]
            i += 2
        elif arg.startswith("http://") or arg.startswith("https://"):
            url = arg
            i += 1
        else:
            i += 1
            
    payload_bytes = None
    if data:
        cleaned_json = clean_powershell_json(data)
        payload_bytes = cleaned_json.encode("utf-8")
        
    req = urllib.request.Request(url, data=payload_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            print(body)
        except:
            print(f"HTTP/1.1 {e.code} {e.reason}")
    except Exception as e:
        print(f"Erro de conexão: {e}")

if __name__ == "__main__":
    main()
