import argparse
import os
import json
from extract_code import * # get_project_structure, analyze_dependencies, process_atlas_data
from code_search import CodeSearcher
import subprocess

import shutil
import tempfile

def get_project_structure(project_path):
    res = {}
    repo_name = os.path.basename(project_path)

    for root, dirs, files in os.walk(project_path):
        # Trim the root to start from the repository's root directory
        trimmed_root = root[len(project_path):].lstrip(os.sep)
        path_parts = trimmed_root.split(os.sep)
        current_level = res

        # Construct the nested dictionary structure
        for part in path_parts:
            current_level = current_level.setdefault(part, {})

        for file in files:
            try:
                file_path = os.path.join(root, file)
                if file.endswith(".py") or file.endswith(".ipynb"):
                    current_level[file] = get_file_code(file_path)
                elif file.endswith(".md"):
                    current_level[file] = parse_md(file_path)
            except Exception as e:
                print(f"Failed to process file {file_path}: {e}")

    # Wrap in the repository's name
    return {repo_name: res}
def clone_github_repo(github_url, dest_folder):
    """
    Clone a GitHub repository to the specified local directory, even if the directory is not empty.
    """
    try:
        # Create a temporary directory to clone the repo
        with tempfile.TemporaryDirectory() as temp_dir:
            # Clone the repository into the temporary directory
            subprocess.run(["git", "clone", github_url, temp_dir], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Move the contents of the cloned repo to the destination folder
            repo_name = os.path.basename(github_url.rstrip('/').split('/')[-1])
            source_folder = os.path.join(temp_dir, repo_name)
            for item in os.listdir(source_folder):
                s = os.path.join(source_folder, item)
                d = os.path.join(dest_folder, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
            
            print("Repository cloned successfully.")

    except subprocess.CalledProcessError as e:
        print(f"Error in subprocess: {e.stderr.decode().strip()}")
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Parse a project structure into a JSON representation.')
    # parser.add_argument('--github_url', type=str, required=True, help='URL to the GitHub repository.')    
    parser.add_argument('--github_url', type=str, default= "https://github.com/dr-aheydari/SoftAdapt", help='URL to the GitHub repository.')    
    # parser.add_argument('--pdf_path', type=str, required=True, help='Path to the paper PDF')
    # parser.add_argument('--output_dir_path', type=str, required=True, help='Path to the output dir.')
    parser.add_argument('--output_dir_path', type=str, default= r"C:\Users\agianolini\OneDrive - ANDES WEALTH MANAGEMENT SA\Desktop\research-assistant-main", 
                        help='Path to the output dir.')
    parser.add_argument('--model_path', type=str, default=r"C:\Users\agianolini\OneDrive - ANDES WEALTH MANAGEMENT SA\Desktop\research-assistant-main\model (7).bin") # change to your model path
    parser.add_argument('--nl_query', type=str, default='a for loop that prints the world')
    args = parser.parse_args()
    
    temp_dir = r"C:\Users\agianolini\OneDrive - ANDES WEALTH MANAGEMENT SA\Desktop\research-assistant-main\output" # Temporary directory to clone the repo
    clone_github_repo(args.github_url, temp_dir)

    # Get the project structure
    project_structure = get_project_structure(temp_dir)

    # Save the project structure to a JSON file
    os.makedirs(args.output_dir_path, exist_ok=True)
    project_name = os.path.basename(args.github_url)
    output_path = os.path.join(args.output_dir_path, f'{project_name}.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(project_structure, f, ensure_ascii=False, indent=4)
    
    data = {}
    # Leer y analizar el archivo JSON
    try:
       with open(output_path, 'r') as file:
        data = json.load(file)
    except Exception as e:
        print(f"Error al leer el archivo JSON: {e}")

    # Proceso de extracción de fragmentos de código
    code_snippets = []
    try:
    # Iterar sobre todas las claves principales del diccionario JSON
        for main_key in data.keys():
            for filename, content in data[main_key].items():
                if 'functions' in content:
                    for function_name, function_content in content['functions'].items():
                        if 'code' in function_content:
                            code_snippets.append(function_content['code'])
    except Exception as e:
        code_snippets = f"Error al procesar el JSON: {e}"

    searcher = CodeSearcher(args.model_path, code_snippets)
    k=3
    t = searcher.get_similarity_search(args.nl_query, k)

    print("Top K similar items: \n")
    print(t)

if __name__ == '__main__':
    main()

