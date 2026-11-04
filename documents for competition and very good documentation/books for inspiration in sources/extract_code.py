import re
import os
import unicodedata

def extract_code_from_tex(tex_file_path, output_dir="extracted_code"):
    tex_file_path = unicodedata.normalize('NFKC', tex_file_path).replace('\xa0', ' ')
    if not os.path.exists(tex_file_path):
        print(f"File not found: {tex_file_path}")
        return
    
    with open(tex_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    pattern = re.compile(r'\\chapter\{.*?\\code\{(.*?)\}\}.*?\\begin\{lstlisting\}(.*?)\\end\{lstlisting\}', re.DOTALL)
    matches = pattern.findall(content)
    
    if not matches:
        pattern = re.compile(r'\\begin\{lstlisting\}(.*?)\\end\{lstlisting\}', re.DOTALL)
        matches = [("listing_" + str(i+1) + ".py", code) for i, code in enumerate(pattern.findall(content))]

    os.makedirs(output_dir, exist_ok=True)
    
    for filename, code in matches:
        filename = filename.strip()
        clean_filename = os.path.normpath(filename)
        file_path = os.path.join(output_dir, clean_filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as out_f:
            out_f.write(code.strip() + '\n')
        print(f"Extracted: {file_path}")

if __name__ == "__main__":
    import sys
    target_tex = sys.argv[1] if len(sys.argv) > 1 else "guo_code1.tex"
    extract_code_from_tex(target_tex)
