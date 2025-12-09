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
