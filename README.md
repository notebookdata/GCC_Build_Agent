🤖 AI-Powered GCC/CMake Repair Agent
An autonomous agent that compiles C/C++ projects, parses GCC/Clang/Linker errors, and uses a local Large Language Model (LLM) to surgically fix the code.

Designed for Ubuntu 24.04 running on local hardware (NVIDIA RTX 3060) using Ollama and Qwen2.5-Coder.

✨ Features
Autonomic Build Loop: Runs cmake, builds, catches errors, fixes them, and retries.

Deep Error Analysis:

Compilation Errors: Fixes syntax, types, and missing semicolons.

Header Issues: Reads included files to fix visibility/scope issues (e.g., private members).

Linker Errors: Performs a project-wide symbol search to implement missing functions/methods causing undefined reference errors.

Privacy First: Runs 100% locally. Your code never leaves your machine.

Hardware Optimized: Tuned for 12GB VRAM GPUs (RTX 3060).

🛠️ Prerequisites & Environment
This project is optimized for the following environment:

OS: Ubuntu 24.04.3 LTS

Python: 3.13.0

GPU: NVIDIA GeForce RTX 3060 (12GB VRAM)

CUDA: 12.8

Compilers: GCC 13.3.0 / CMake 3.28+

1. Install Ollama (LLM Backend)
The agent relies on Ollama to manage the AI model.

Bash

curl -fsSL https://ollama.com/install.sh | sh
2. Pull the AI Model
We use Qwen2.5-Coder-14B. It is the "sweet spot" for 12GB VRAM, offering "Senior Developer" logic capabilities needed for linker errors.

Bash

ollama pull qwen2.5-coder:14b
Note: If you want faster speed at the cost of reasoning capabilities, you can use qwen2.5-coder:7b.

📦 Installation
1. Clone/Create Project Directory

Bash

mkdir ai_gcc_agent
cd ai_gcc_agent
2. Set up Python Virtual Environment Python 3.13 requires a managed environment.

Bash

python3 -m venv venv
source venv/bin/activate
3. Install Dependencies

Bash

pip install ollama
4. Add the Agent Script Save the final agent code (version 4) as builder.py in this directory.

🚀 Usage
1. Prepare your CMake Project Ensure your project has a CMakeLists.txt in the root directory.

2. Run the Agent The agent will automatically create a build/ directory, configure the project, and start the repair loop.

Bash

python builder.py
The Automation Process

Shutterstock
Configure: Runs cmake -S . -B build.

Build: Runs cmake --build build.

Analyze: If the build fails:

Identifies the error type (Compile vs. Linker).

Locates the broken file.

If Linker Error: Scans the whole project for the missing symbol's declaration.

If Compile Error: Reads the source file + related headers.

Fix: Sends context to qwen2.5-coder:14b via Ollama.

Apply: Overwrites the file with the fix and loops back to Step 2.

🧪 Test Case: "The Broken Matrix"
To verify the agent works, create this intentionally broken project structure:

File Structure:

Plaintext

.
├── CMakeLists.txt
├── builder.py
├── include
│   └── matrix.hpp   <-- Contains Syntax & Logic Errors
└── src
    ├── main.cpp     <-- Contains Linker Error (Missing implementation)
    └── utils.cpp    <-- Contains Scope Error (Private access)
Run the Agent:

Bash

python builder.py
Expected Outcome:

Attempt 1: Fails on utils.cpp (Private member access). → Agent adds getter to matrix.hpp and updates utils.cpp.

Attempt 2: Fails on matrix.hpp (Missing semicolon). → Agent fixes header.

Attempt 3: Fails on Linker (Undefined specializedSolver). → Agent scans project, sees declaration in matrix.hpp, and implements the function body in a .cpp file.

Attempt 4: Build Success! ✅

⚙️ Configuration
You can tweak the settings at the top of builder.py:

Python

# Change model size (use 7b for speed, 32b for massive tasks if you upgrade GPU)
MODEL_NAME = "qwen2.5-coder:14b" 

# Context window size (increase for very large files)
options={'num_ctx': 8192}










This is a very common scenario in enterprise or university environments.

Since Ollama is distributed as a single binary file, you do not need root (sudo) access to install it. You can run it entirely from your home directory.

Here are the two best ways to handle this:

Option 1: Run Ollama Locally (If the new machine has a GPU)
If this new machine has a decent GPU, you can simply download the binary and run it manually.

1. Download the Binary Run this in your terminal to download the Linux binary to your current folder:

Bash

curl -L https://ollama.com/download/ollama-linux-amd64 -o ollama
2. Make it Executable

Bash

chmod +x ollama
3. Start the Server You need to run the server in the background (or in a separate terminal window).

Bash

./ollama serve &
(The & puts it in the background. If you want to see logs, remove the & and open a new terminal tab).

4. Pull the Model Now you can use the ./ollama command just like the system version:

Bash

./ollama pull qwen2.5-coder:14b
5. Update Python Script You don't need to change builder.py. The Python ollama library looks for localhost:11434 by default, which your local binary is now serving.

Option 2: Remote Mode (Use your RTX 3060 Machine as the Brain)
If the new machine is a weak laptop or a server with no GPU, you shouldn't run the model there. Instead, you can run the agent code on the new machine, but have it send the code to your RTX 3060 machine for processing.

Step A: Configure the RTX 3060 Machine (The Server)

Stop Ollama if it's running.

Run Ollama with a special environment variable to allow outside connections (by default, it only listens to itself).

Bash

OLLAMA_HOST=0.0.0.0 ollama serve
Find this machine's IP address (e.g., run ip a, let's assume it is 192.168.1.50).

Step B: Configure the New Machine (The Client) You don't need to install Ollama binaries here at all! You only need the Python script.

Set the Environment Variable: Tell the Python library where the "Brain" is.

Bash

export OLLAMA_HOST=192.168.1.50:11434
Run the Agent:

Bash

python builder.py
Step C: (Optional) Update builder.py Hardcoding If you don't want to export the variable every time, you can modify builder.py to point to the specific IP:

Python

# Inside builder.py
import ollama

# Create a client instance pointing to your GPU machine
client = ollama.Client(host='http://192.168.1.50:11434')

# Then update the chat call:
response = client.chat( ... ) 
# Instead of ollama.chat(...)
Summary Recommendation
If the new machine has a GPU: Use Option 1 (Download binary -> chmod +x -> Run).

If the new machine has NO GPU: Use Option 2 (Point it to your RTX 3060 machine).
