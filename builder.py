import subprocess
import sys
import ollama
import os
import re
import shutil

# --- Configuration ---
MODEL_NAME = "qwen2.5-coder:14b"
#MODEL_NAME = "qwen2.5-coder:7b"
BUILD_DIR = "build"

# Regex to find file paths in GCC/Clang error output
# Matches: /path/to/file.cpp:10:5: error: message
ERROR_PATTERN = re.compile(r"^([^:\n]+):(\d+):(\d+):\s+(?:fatal\s+)?error:\s+(.+)$", re.MULTILINE)

def run_command(command, cwd="."):
    """Runs a shell command and returns (success, output)."""
    print(f"⚙️  Running: {' '.join(command)}")
    result = subprocess.run(
        command, 
        cwd=cwd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, # Merge stderr into stdout for easier parsing
        text=True
    )
    return result.returncode == 0, result.stdout

def find_culprit_file(build_log):
    """Parses build log to find the first file that failed to compile."""
    match = ERROR_PATTERN.search(build_log)
    if match:
        file_path = match.group(1)
        line_num = match.group(2)
        error_msg = match.group(4)
        
        # Ensure path is relative to current directory if possible
        if os.path.isabs(file_path):
            try:
                file_path = os.path.relpath(file_path, os.getcwd())
            except ValueError:
                pass # Keep absolute if on different drive/path
                
        return file_path, line_num, error_msg
    return None, None, None

def get_ai_fix(code_content, error_log, file_path):
    """Sends the broken file and error log to the AI."""
    print(f"🤖 Agent is analyzing {file_path}...")
    
    prompt = f"""
    You are an expert C++ developer using CMake.
    The build failed for file: {file_path}
    
    --- CODE CONTENT ---
    {code_content}
    
    --- BUILD ERROR ---
    {error_log}
    
    **INSTRUCTIONS:**
    1. Fix the error in the code.
    2. Maintain existing logic and style.
    3. Output ONLY the complete, fixed file content inside a markdown block.
    """
    
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{'role': 'user', 'content': prompt}],
        options={'temperature': 0.0} # Strict mode
    )
    
    return response['message']['content']

def extract_code(response_text):
    """Clean markdown formatting from response."""
    if "```" in response_text:
        # Robust extraction for ```cpp, ```c, or just ```
        return response_text.split("```")[1].split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return response_text

def build_project():
    """Orchestrates the CMake build process."""
    
    # 1. Check for CMakeLists.txt
    if not os.path.exists("CMakeLists.txt"):
        print("❌ No CMakeLists.txt found. Is this a CMake project?")
        return False

    # 2. Configure (cmake -S . -B build)
    if not os.path.exists(BUILD_DIR):
        os.makedirs(BUILD_DIR)
        
    print("configure...")
    success, config_log = run_command(["cmake", "-S", ".", "-B", BUILD_DIR])
    if not success:
        print("❌ CMake Configuration Failed!")
        print(config_log)
        return False

    # 3. Build (cmake --build build)
    print("building...")
    success, build_log = run_command(["cmake", "--build", BUILD_DIR])
    
    if success:
        print("\n✅ Build Successful! No errors found.")
        return True
    
    print("\n❌ Build Failed. Analyzing errors...")
    
    # 4. Find the broken file
    file_path, line, msg = find_culprit_file(build_log)
    
    if not file_path:
        print("⚠️  Could not automatically identify the source file from the error log.")
        print("Here is the log tail:")
        print(build_log[-500:])
        return False

    print(f"👉 Error found in: {file_path} (Line {line})")
    print(f"👉 Error message: {msg}")

    # 5. Read Broken File
    try:
        with open(file_path, "r") as f:
            original_code = f.read()
    except FileNotFoundError:
        print(f"❌ Could not open source file: {file_path}")
        return False

    # 6. Get Fix from AI
    ai_response = get_ai_fix(original_code, build_log, file_path)
    fixed_code = extract_code(ai_response)

    # 7. Apply Fix
    shutil.copy(file_path, file_path + ".bak") # Backup
    with open(file_path, "w") as f:
        f.write(fixed_code)
        
    print(f"✨ Applied fix to {file_path}")
    
    # 8. Recursive check? (Optional, let's just return for now)
    return False # Return False to indicate we had to fix something

def main():
    MAX_ATTEMPTS = 3
    attempt = 1
    
    while attempt <= MAX_ATTEMPTS:
        print(f"\n[Attempt {attempt}/{MAX_ATTEMPTS}]")
        success = build_project()
        
        if success:
            print(f"🚀 Project built successfully on attempt {attempt}!")
            sys.exit(0)
            
        attempt += 1
        
    print("\n❌ Failed to fix project after maximum attempts.")
    sys.exit(1)

if __name__ == "__main__":
    main()
