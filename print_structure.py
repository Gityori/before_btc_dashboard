import os

def print_directory_structure(startpath, exclude_dirs=None):
    if exclude_dirs is None:
        exclude_dirs = []

    for root, dirs, files in os.walk(startpath):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]  # 除外するディレクトリをフィルタリング
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print(f"{subindent}{f}")

if __name__ == "__main__":
    # スクリプトが存在するディレクトリのパスを取得
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 親ディレクトリ（プロジェクトのルートディレクトリ）のパスを取得
    project_root = os.path.dirname(current_dir)
    
    # 除外したいディレクトリがあれば、ここにリストとして追加
    exclude_dirs = ['.git', '__pycache__', 'venv']

    print("Project Structure:")
    print_directory_structure(project_root, exclude_dirs)