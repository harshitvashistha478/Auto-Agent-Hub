from src.utils.state import AgentHubState
from src.llm.llms import architecture_llm, codegen_llm, error_analysis_llm
from src.utils.prompts import architecture_prompt, codegen_prompt, error_analysis_prompt, fix_errors_prompt

import os
import re
import json
import shutil

from typing import List, Dict
from pathlib import Path


# Architecture node

def get_architecture(state: AgentHubState):
    response = architecture_llm.invoke(architecture_prompt(state['user_idea']))
    state['architecture'] = response
    return state


# Codegen node

def parse_files_from_response(response_text: str) -> List[Dict[str, str]]:
    """
    Extracts file paths and code blocks from LLM output.
    Supports multiple formats:
    - <file:path> ... ```language\ncode\n```
    - <file:path>\n```language\ncode\n```
    - **path**\n```language\ncode\n```
    """
    
    # # Debug: Print first 500 chars of response
    # print("=" * 60)
    # print("📝 LLM Response Preview (first 500 chars):")
    # print("=" * 60)
    # print(response_text[:500])
    # print("=" * 60)
    
    files = []
    
    pattern1 = r"<file:([^\>]+)>\s*```[\w]*\n(.*?)```"
    matches1 = re.findall(pattern1, response_text, re.DOTALL)
    
    if matches1:
        # print(f"✅ Found {len(matches1)} files using Pattern 1 (<file:path>)")
        for path, content in matches1:
            files.append({
                "path": path.strip(),
                "content": content.strip()
            })
        return files
    
    pattern2 = r"(?:File:|file:|Path:|path:)?\s*[`\"']?([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+)[`\"']?\s*```[\w]*\n(.*?)```"
    matches2 = re.findall(pattern2, response_text, re.DOTALL)
    
    if matches2:
        # print(f"✅ Found {len(matches2)} files using Pattern 2 (flexible path matching)")
        for path, content in matches2:
            files.append({
                "path": path.strip(),
                "content": content.strip()
            })
        return files
    
    pattern3 = r"#+\s+([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+)\s*```[\w]*\n(.*?)```"
    matches3 = re.findall(pattern3, response_text, re.DOTALL)
    
    if matches3:
        # print(f"✅ Found {len(matches3)} files using Pattern 3 (markdown headers)")
        for path, content in matches3:
            files.append({
                "path": path.strip(),
                "content": content.strip()
            })
        return files
    
    # print("❌ No files matched any pattern!")
    # print("\n🔍 Checking for code blocks in response:")
    code_blocks = re.findall(r"```[\w]*\n(.*?)```", response_text, re.DOTALL)
    # print(f"   Found {len(code_blocks)} code blocks total")
    
    # print("\n🔍 Checking for file-like paths:")
    paths = re.findall(r"[a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+", response_text)
    # print(f"   Found {len(paths)} potential file paths: {paths[:5]}")
    
    return files


def write_files_to_directory(files: List[Dict[str, str]], base_dir: str = "my_project"):
    """
    Writes parsed files into a base directory.
    Automatically detects project root folder name if present.
    """
    if not files:
        print("⚠️  No files parsed from LLM output.")
        return

    first_path = files[0]["path"]
    if "/" in first_path:
        detected_root = first_path.split("/")[0]
        if detected_root not in ["src", "app", "lib", "tests", "docs"]:
            base_dir = detected_root
    
    # print(f"📁 Using base directory: {base_dir}")

    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
        # print(f"🗑️  Removed existing directory: {base_dir}")
    
    os.makedirs(base_dir, exist_ok=True)

    for idx, file in enumerate(files, 1):
        relative_path = file["path"]
        
        if relative_path.startswith(base_dir + "/"):
            relative_path = relative_path[len(base_dir) + 1:]

        file_path = os.path.join(base_dir, relative_path)
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file["content"])
        
        # print(f"   [{idx}/{len(files)}] ✅ {relative_path} ({len(file['content'])} chars)")

    print(f"\n✅ Code written to: {os.path.abspath(base_dir)}")


def generate_code(state: AgentHubState) -> AgentHubState:
    """
    Uses the architecture output to generate full project code
    and writes it into the local filesystem.
    """
    architecture = state["architecture"]

    print("🚀 Entered code generation node...")
    response = codegen_llm.invoke(codegen_prompt(architecture))

    response_text = getattr(response, "content", str(response))

    files = parse_files_from_response(response_text)

    write_files_to_directory(files)

    state["code_generated"] = False
    print("✅ Code generation completed.")
    return state


# Error Analysis Node

def check_errors(state: AgentHubState) -> AgentHubState:
    """Enhanced error checking with iteration tracking"""
    print("🔍 Starting LLM-based error analysis...")
    print("="*60)
    
    base_dir = "my_project"
    error_dict = {}
    total_files = 0
    files_with_errors = 0
    
    # Track iteration history
    iteration = state.get("iteration_count", 0)
    error_history = state.get("error_history", {})
    
    print(f"🔄 Iteration: {iteration}")
    
    if not os.path.exists(base_dir):
        print(f"❌ Directory {base_dir} does not exist!")
        state["errors"] = {"_global": ["Project directory not found"]}
        return state
    
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']]
        
        for file in files:
            if file.startswith('.') or file.endswith(('.pyc', '.pyo', '.pyd', '.so', '.dll', '.backup')):
                continue
            
            ext = Path(file).suffix.lower()
            if ext not in ['.py', '.js', '.jsx', '.ts', '.tsx', '.json', '.yaml', '.yml', 
                          '.html', '.css', '.java', '.cpp', '.c', '.h', '.go', '.rs', '.rb']:
                continue
            
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, base_dir)
            
            total_files += 1
            print(f"\n📄 Analyzing: {relative_path}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code_content = f.read()
                
                # Get previous errors for this file
                previous_errors = error_history.get(relative_path, [])
                
                # Use enhanced prompt with context
                prompt = error_analysis_prompt(relative_path, code_content, previous_errors)
                response = error_analysis_llm.invoke(prompt)
                
                response_text = getattr(response, "content", str(response))
                
                try:
                    if "```json" in response_text:
                        json_start = response_text.find("```json") + 7
                        json_end = response_text.find("```", json_start)
                        response_text = response_text[json_start:json_end].strip()
                    elif "```" in response_text:
                        json_start = response_text.find("```") + 3
                        json_end = response_text.find("```", json_start)
                        response_text = response_text[json_start:json_end].strip()
                    
                    errors = json.loads(response_text)
                    
                    if not isinstance(errors, list):
                        errors = [str(errors)]
                    
                except json.JSONDecodeError:
                    print(f"   ⚠️  Could not parse JSON response")
                    errors = []
                
                if errors:
                    error_dict[relative_path] = errors
                    files_with_errors += 1
                    
                    # Compare with previous iteration
                    prev_count = len(previous_errors)
                    curr_count = len(errors)
                    
                    if previous_errors:
                        if curr_count < prev_count:
                            print(f"   ✅ Improved! {prev_count} → {curr_count} errors")
                        elif curr_count > prev_count:
                            print(f"   ⚠️  Worse! {prev_count} → {curr_count} errors")
                        else:
                            print(f"   ⚡ Same: {curr_count} errors")
                    else:
                        print(f"   ❌ Found {len(errors)} issue(s)")
                    
                    for i, error in enumerate(errors[:2], 1): 
                        print(f"      {i}. {error}")
                    if len(errors) > 2:
                        print(f"      ... and {len(errors) - 2} more")
                else:
                    print(f"   ✅ No errors found")
            
            except Exception as e:
                print(f"   ⚠️  Error analyzing file: {str(e)}")
    
    # Calculate overall progress
    total_errors_now = sum(len(errs) for errs in error_dict.values())
    total_errors_prev = sum(len(errs) for errs in error_history.values())
    
    print("\n" + "="*60)
    print(f"📊 Analysis Summary (Iteration {iteration}):")
    print(f"   Total files analyzed: {total_files}")
    print(f"   Files with issues: {files_with_errors}")
    print(f"   Files without issues: {total_files - files_with_errors}")
    
    if iteration > 0:
        print(f"\n   📈 Progress:")
        print(f"   Previous total errors: {total_errors_prev}")
        print(f"   Current total errors: {total_errors_now}")
        if total_errors_now < total_errors_prev:
            improvement = total_errors_prev - total_errors_now
            print(f"   ✅ IMPROVED by {improvement} errors ({improvement/max(total_errors_prev,1)*100:.1f}%)")
        elif total_errors_now > total_errors_prev:
            regression = total_errors_now - total_errors_prev
            print(f"   ⚠️  REGRESSED by {regression} errors")
        else:
            print(f"   ⚡ No change in error count")
    
    print("="*60)
    
    if error_dict:
        print("\n⚠️  Issues found in:")
        for filename, errors in error_dict.items():
            print(f"   📄 {filename}: {len(errors)} issue(s)")
    else:
        state['code_generated'] = True
        print("\n✅ All files passed LLM validation!")
    
    state["errors"] = error_dict
    state["error_history"] = error_dict.copy()  # Store for next iteration
    print("\n✅ Error analysis completed.")
    return state


# Validation Node


def testing(state: AgentHubState) -> AgentHubState:
    """
    Test for edge cases if code is generated successful and error-free.
    """
    print("Ready with production ready code")
    return state


def handle_errors(state: AgentHubState) -> AgentHubState:
    """Enhanced error fixing with better tracking"""
    error_dict = state.get("errors", {})
    
    if not error_dict:
        print("✅ No errors to fix!")
        state["errors_fixed"] = True
        return state
    
    iteration = state.get("iteration_count", 0)
    fix_history = state.get("fix_history", {})
    
    print("🔧 Starting error fixing process...")
    print(f"🔄 Iteration: {iteration}")
    print("="*60)
    
    base_dir = "my_project"
    fixed_files = []
    failed_files = []
    total_errors_fixed = 0
    
    # Limit iterations to prevent infinite loops
    MAX_ITERATIONS = 5
    if iteration >= MAX_ITERATIONS:
        print(f"⚠️  Reached maximum iterations ({MAX_ITERATIONS}). Stopping.")
        state["errors_fixed"] = True
        return state
    
    for filename, errors in error_dict.items():
        if not errors: 
            continue
        
        file_path = os.path.join(base_dir, filename)
        
        print(f"\n📄 Fixing: {filename}")
        print(f"   Errors to fix: {len(errors)}")
        
        try:
            if not os.path.exists(file_path):
                print(f"   ❌ File not found: {file_path}")
                failed_files.append(filename)
                continue
            
            with open(file_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
            
            
            # Get fix history for this file
            file_history = fix_history.get(filename, [])
            
            print(f"   🤖 Requesting LLM to fix errors...")
            prompt = fix_errors_prompt(filename, original_code, errors, iteration, file_history)
            response = codegen_llm.invoke(prompt)
            
            fixed_code = getattr(response, "content", str(response))
            
            # Clean markdown if present
            if "```" in fixed_code:
                lines = fixed_code.split('\n')
                in_code_block = False
                code_lines = []
                
                for line in lines:
                    if line.strip().startswith('```'):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block or (not in_code_block and '```' not in line):
                        code_lines.append(line)
                
                fixed_code = '\n'.join(code_lines)
            
            fixed_code = fixed_code.strip()
            
            # Validate the fix isn't empty or too different
            if not fixed_code or len(fixed_code) < len(original_code) * 0.3:
                print(f"   ⚠️  Fix seems invalid (too small), keeping original")
                failed_files.append(filename)
                continue
            
            # Write fixed code
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_code)
            
            # Update history
            file_history.append(f"Iteration {iteration}: Fixed {len(errors)} errors")
            fix_history[filename] = file_history
            
            fixed_files.append(filename)
            total_errors_fixed += len(errors)
            print(f"   ✅ Fixed and saved successfully!")
            print(f"      Lines: {len(original_code.splitlines())} → {len(fixed_code.splitlines())}")
        
        except Exception as e:
            print(f"   ❌ Failed to fix: {str(e)}")
            failed_files.append(filename)
            
            # Restore from latest backup
            backup_path = file_path + f".backup_iter{iteration}"
            if os.path.exists(backup_path):
                try:
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        original = f.read()
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(original)
                    print(f"   🔄 Restored from backup")
                except:
                    pass
    
    print("\n" + "="*60)
    print(f"📊 Fixing Summary (Iteration {iteration}):")
    print(f"   Total files processed: {len(error_dict)}")
    print(f"   Successfully fixed: {len(fixed_files)}")
    print(f"   Failed to fix: {len(failed_files)}")
    print(f"   Total errors addressed: {total_errors_fixed}")
    print("="*60)
    
    if fixed_files:
        print("\n✅ Successfully fixed:")
        for filename in fixed_files:
            print(f"   📄 {filename}")
    
    if failed_files:
        print("\n❌ Failed to fix:")
        for filename in failed_files:
            print(f"   📄 {filename}")
    
    # Clear errors for next check
    state["errors"] = {}
    state["fix_history"] = fix_history
    state["iteration_count"] = iteration + 1
    
    return state

