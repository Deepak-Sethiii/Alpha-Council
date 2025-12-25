# debug_mcp.py
import sys
import os
import json
import subprocess

def debug_server():
    print("🕵️ DIAGNOSTIC: Testing Finance Server (With Handshake)...")
    
    server_path = os.path.join("nexus", "servers", "finance_server.py")
    if not os.path.exists(server_path):
        print(f"❌ ERROR: File not found at {server_path}")
        return

    # --- THE 3-STEP HANDSHAKE ---
    
    # 1. "Hello" (Initialize)
    msg_1 = {
        "jsonrpc": "2.0", 
        "id": 1, 
        "method": "initialize", 
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "debug-client", "version": "1.0"}
        }
    }
    
    # 2. "I heard you" (Notification)
    msg_2 = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }
    
    # 3. "Do the work" (Tool Call)
    msg_3 = {
        "jsonrpc": "2.0", 
        "id": 2, 
        "method": "tools/call", 
        "params": {
            "name": "analyze_stock",
            "arguments": {"ticker": "NVDA"} 
        }
    }
    
    # Send all as newline-delimited JSON
    payload = json.dumps(msg_1) + "\n" + json.dumps(msg_2) + "\n" + json.dumps(msg_3) + "\n"

    print(f"📤 Sending Handshake + Request...")

    # Environment
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        process = subprocess.Popen(
            [sys.executable, server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            encoding='utf-8'
        )
        
        stdout, stderr = process.communicate(input=payload)
        
        print("\n--- SERVER RESPONSE (STDOUT) ---")
        # Parse the output line by line to find the result
        lines = stdout.strip().split("\n")
        found_result = False
        
        for line in lines:
            try:
                data = json.loads(line)
                # We are looking for the response to ID 2 (The tool call)
                if data.get("id") == 2:
                    if "result" in data:
                        print("✅ SUCCESS! Server returned data:")
                        print(data["result"]["content"][0]["text"][:200] + "...")
                        found_result = True
                    elif "error" in data:
                        print("❌ SERVER ERROR:")
                        print(data["error"])
            except:
                pass
                
        if not found_result:
            print("⚠️ Parsed output but didn't find a result for ID 2.")
            print("Raw Output:", stdout)
            
        if stderr:
            print("\n--- STDERR LOGS ---")
            print(stderr)

    except Exception as e:
        print(f"\n❌ Execution Failed: {e}")

if __name__ == "__main__":
    debug_server()