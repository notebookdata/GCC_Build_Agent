import subprocess
import sys
import ollama
import os
import re
import shutil

# Configuration
MODEL_NAME = "qwen2.5-coder:14b" # 14B is recommended for multi-file reasoning
BUILD_DIR = "build"

# Regex to find file paths in error output
ERROR_PATTERN = re.compile(r"^([^:\n]+):(\d+):(\d+):\s+(?:fatal\s+)?error:\s+(.+)$", re.MULTILINE)
# Regex to find local includes: #include "../include/matrix.hpp"
INCLUDE_PATTERN = re.compile(r'#include\s+"([^"]+)"')

def run_command(command, cwd="."):
    """Runs a shell command and returns (success, output)."""
    print(f"⚙️  Running: {' '.join(command)}")
    result = subprocess.run(
        command, 
        cwd=cwd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, 
        text=True
    )
    return result.returncode == 0, result.stdout

def find_culprit_file(build_log):
    """Parses build log to find the first broken file."""
    match = ERROR_PATTERN.search(build_log)
    if match:
        return match.group(1), match.group(2), match.group(4)
    return None, None, None

def get_related_headers(source_code, source_dir):
    """Scans code for #include "..." and resolves their paths."""
    headers = {}
    matches = INCLUDE_PATTERN.findall(source_code)
    for header_path in matches:
        # Resolve relative path
        full_path = os.path.normpath(os.path.join(source_dir, header_path))
        if os.path.exists(full_path):
            with open(full_path, "r") as f:
                headers[full_path] = f.read()
    return headers

def get_ai_fix(source_path, source_code, headers, error_log):
    """Sends source + headers to AI and asks for multi-file fixes."""
    print(f"🤖 Analyzing {source_path} and {len(headers)} related headers...")
    
    # Construct context with Source File + Headers
    context_str = f"--- MAIN SOURCE FILE: {source_path} ---\n{source_code}\n\n"
    for path, content in headers.items():
        context_str += f"--- LINKED HEADER: {path} ---\n{content}\n\n"
    
    prompt = f"""
    You are an expert C++ Build Agent. The build failed.
    
    CONTEXT:
    {context_str}
    
    ERROR LOG:
    {error_log}
    
    INSTRUCTIONS:
    1. You may need to modify the Source File, the Header File, or BOTH.
    2. If you need to add a method (like a getter) to a class, add it to the Header.
    3. Output the FULL content of ANY file you modify.
    4. Use this specific format for your output:
    
    FILE: <path_to_file>
    ```cpp
    ... full new content of file ...
    ```
    
    (Repeat the above block for every file that needs changing)
    """
    
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{'role': 'user', 'content': prompt}],
        options={'temperature': 0.0, 'num_ctx': 8192} 
    )
    return response['message']['content']

def parse_and_apply_fixes(ai_response):
    """Splits AI response into multiple files and saves them."""
    # Split by "FILE: " marker
    parts = re.split(r'FILE:\s*([^\s\n]+)', ai_response)
    
    if len(parts) < 2:
        print("⚠️  AI did not return valid file format.")
        return False

    # The split creates [preamble, filename1, content1, filename2, content2...]
    # We skip index 0 (preamble) and iterate in pairs
    for i in range(1, len(parts), 2):
        filename = parts[i].strip()
        content_block = parts[i+1]
        
        # Extract code from markdown
        if "```" in content_block:
            code = content_block.split("```")[1]
            if code.startswith("cpp") or code.startswith("c"):
                code = code.split("\n", 1)[1]
            code = code.rsplit("```", 1)[0]
        else:
            code = content_block
            
        print(f"📝 Agent is rewriting: {filename}")
        
        # Backup
        if os.path.exists(filename):
            shutil.copy(filename, filename + ".bak")
            
        # Write
        with open(filename, "w") as f:
            f.write(code.strip())
            
    return True

def build_project():
    if not os.path.exists("CMakeLists.txt"):
        print("❌ No CMakeLists.txt found.")
        return False

    if not os.path.exists(BUILD_DIR):
        os.makedirs(BUILD_DIR)
        
    print("configure...")
    success, _ = run_command(["cmake", "-S", ".", "-B", BUILD_DIR])
    
    print("building...")
    success, build_log = run_command(["cmake", "--build", BUILD_DIR])
    
    if success:
        print("\n✅ Build Successful!")
        return True
    
    print("\n❌ Build Failed.")
    
    # 1. Identify Broken File
    file_path, line, msg = find_culprit_file(build_log)
    if not file_path:
        print("⚠️  Could not identify source file.")
        print(build_log[-500:])
        return False

    print(f"👉 Error in: {file_path} (Line {line}): {msg}")

    # 2. Read Source Code
    try:
        with open(file_path, "r") as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"❌ Cannot open {file_path}")
        return False

    # 3. Read Related Headers (The Magic Step)
    headers = get_related_headers(source_code, os.path.dirname(file_path))
    
    # 4. Ask AI
    ai_response = get_ai_fix(file_path, source_code, headers, build_log)
    
    # 5. Apply Fixes
    files_fixed = parse_and_apply_fixes(ai_response)
    
    return False

def main():
    MAX_ATTEMPTS = 5
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\n[Attempt {attempt}/{MAX_ATTEMPTS}]")
        if build_project():
            sys.exit(0)
            
    print("\n❌ Max attempts reached.")
    sys.exit(1)

if __name__ == "__main__":
    main()
