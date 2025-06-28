# Copy Contents for LLVM

This script helps you collect code and documentation from the project for sharing with Large Language Models (LLMs).

## Overview

`copy_contents_for_llvm.sh` is a utility script that:

1. Finds all Python (`.py`), Markdown (`.md`), and text (`.txt`) files in the current directory and subdirectories
2. Excludes files in the `.venv` directory to avoid including virtual environment files
3. For each file, outputs the filename in square brackets followed by the file's contents
4. Copies all this output to the clipboard

This is particularly useful when you want to share your codebase with an LLM for analysis, code review, or assistance.

## Requirements

- macOS (the script uses `pbcopy`, which is specific to macOS)
- Bash shell

## Usage

1. Make sure the script is executable:
   ```bash
   chmod +x copy_contents_for_llvm.sh
   ```

2. Run the script from the root directory of your project:
   ```bash
   ./copy_contents_for_llvm.sh
   ```

3. The contents of your project files will be copied to your clipboard, ready to be pasted into an LLM interface.

## Limitations

- The script only works on macOS due to the use of `pbcopy`
- Only `.py`, `.md`, and `.txt` files are included
- Files in the `.venv` directory are excluded
- Large projects may exceed the context window of some LLMs

## Customization

If you need to include different file types or exclude additional directories, you can modify the script accordingly:

- To include additional file types, add them to the `-name` patterns
- To exclude additional directories, add more `-not -path` conditions
