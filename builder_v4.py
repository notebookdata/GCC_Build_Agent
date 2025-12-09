import subprocess
import sys
import ollama
import os
import re
import shutil

# --- Configuration ---
MODEL_NAME = "qwen2.5-coder:14b"
BUILD_DIR = "build"
EXTENSIONS = {".cpp", ".c", ".cc", ".cxx", ".hpp", ".h"}

# --- Regex Patterns ---
# GCC/Clang Compile Error: /path/to/file:10:5: error: msg
COMPILE_ERROR_PATTERN = re.compile(r"^([^:\n]+):(\d+):(\d+):\s+(?:fatal\s+)?error:\s+(.+)$", re.MULTILINE)

# Linker Error (Standard ld): undefined reference to `Symbol'
# Linker Error (Modern ld/lld): ld: error: undefined symbol: Symbol
LINKER_ERROR_PATTERN = re.compile(r"(?:undefined reference to|undefined symbol:)\s+[`']?([^'\n]+)['`]?")

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

def get_all_source_files(root_dir="."):
    """Recursively finds all C/C++ source files."""
    sources = []
    for root, _, files in os.walk(root_dir):
        if "build" in root or ".git" in root: continue
        for file in files:
            if os.path.splitext(file)[1] in EXTENSIONS:
                sources.append(os.path.join(root, file))
    return sources

def search_symbol_in_project(symbol, root_dir="."):
    """Finds which file declares/uses the missing symbol."""
    # Clean symbol (remove arguments for loose search)
    clean_symbol = symbol.split("(")[0].strip()
    matches = {}
    
    print(f"🔎 Scanning project for symbol: '{clean_symbol}'...")
    
    for file_path in get_all_source_files(root_dir):
        try:
            with open(file_path, "r") as f:
                content = f.read()
                if clean_symbol in content:
                    matches[file_path] = content
        except Exception:
            pass
            
    return matches

def get_ai_fix(context_files, error_log, error_type="compile"):
    """Smart prompt that handles both Compile and Linker errors."""
    
    context_str = ""
    for fpath, content in context_files.items():
        context_str += f"--- FILE: {fpath} ---\n{content}\n\n"

    if error_type == "linker":
        instruction = """
        This is a LINKER ERROR (Undefined Symbol).
        The symbol is likely declared but NOT implemented.
        
        TASK:
        1. Identify the missing function implementation.
        2. You must IMPLEMENT the missing function in a .cpp file.
        3. If the function is in a library, you might need to add it to 'src/utils.cpp' or similar.
        4. Output the FULL content of the file you are modifying.
        """
    else:
        instruction = """
        This is a COMPILATION ERROR.
        TASK: Fix the syntax/logic error in the specified file.
        """

    prompt = f"""
    You are an expert C++ Build Agent.
    
    {instruction}
    
    ERROR LOG:
    {error_log}
    
    PROJECT CONTEXT:
    {context_str}
    
    OUTPUT FORMAT:
    FILE: <path_to_file_to_edit>
    ```cpp
    ... full content ...
    ```
    """
    
    print(f"🤖 Agent is thinking (Mode: {error_type})...")
    
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{'role': 'user', 'content': prompt}],
        options={'temperature': 0.0, 'num_ctx': 8192}
    )
    return response['message']['content']

def apply_fixes(ai_response):
    """Parses AI response and writes files."""
    parts = re.split(r'FILE:\s*([^\s\n]+)', ai_response)
    if len(parts) < 2: return False

    for i in range(1, len(parts), 2):
        filename = parts[i].strip()
        raw_content = parts[i+1]
        
        # Clean Code Block
        if "```" in raw_content:
            code = raw_content.split("```")[1]
            if code.startswith("cpp") or code.startswith("c"):
                code = code.split("\n", 1)[1]
            code = code.rsplit("```", 1)[0]
        else:
            code = raw_content
            
        print(f"💾 Writing fix to: {filename}")
        with open(filename, "w") as f:
            f.write(code.strip())
            
    return True

def build_project():
    if not os.path.exists(BUILD_DIR): os.makedirs(BUILD_DIR)
    
    # 1. Configure
    run_command(["cmake", "-S", ".", "-B", BUILD_DIR])
    
    # 2. Build
    success, log = run_command(["cmake", "--build", BUILD_DIR])
    
    if success:
        print("\n✅ Build Success!")
        return True, None
        
    print("\n❌ Build Failed.")
    return False, log

def analyze_and_fix(build_log):
    # Check for Compile Errors (Files with line numbers)
    compile_match = COMPILE_ERROR_PATTERN.search(build_log)
    if compile_match:
        broken_file = compile_match.group(1)
        print(f"👉 Compile Error in: {broken_file}")
        
        # Read broken file + headers
        files = {broken_file: open(broken_file).read()}
        
        # Simple heuristic: grab headers included in broken file
        base_dir = os.path.dirname(broken_file)
        for line in files[broken_file].splitlines():
            if '#include "' in line:
                h_name = line.split('"')[1]
                h_path = os.path.join(base_dir, h_name)
                if os.path.exists(h_path):
                    files[h_path] = open(h_path).read()
                    
        return get_ai_fix(files, build_log, "compile")

    # Check for Linker Errors (Undefined symbols)
    linker_match = LINKER_ERROR_PATTERN.search(build_log)
    if linker_match:
        missing_symbol = linker_match.group(1)
        print(f"👉 Linker Error: Undefined symbol '{missing_symbol}'")
        
        # Search EVERYWHERE for this symbol
        related_files = search_symbol_in_project(missing_symbol)
        
        if not related_files:
            print("⚠️ Symbol not found in project text. It might be a missing library in CMakeLists.txt")
            # Fallback: Send CMakeLists.txt
            related_files["CMakeLists.txt"] = open("CMakeLists.txt").read()
            
        return get_ai_fix(related_files, build_log, "linker")

    print("⚠️ Unknown error type. Cannot fix.")
    return None

def main():
    MAX_ATTEMPTS = 5
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\n=== Attempt {attempt}/{MAX_ATTEMPTS} ===")
        success, log = build_project()
        
        if success:
            sys.exit(0)
            
        fix_response = analyze_and_fix(log)
        if fix_response:
            apply_fixes(fix_response)
        else:
            print("❌ Agent could not generate a fix.")
            sys.exit(1)

if __name__ == "__main__":
    main()
