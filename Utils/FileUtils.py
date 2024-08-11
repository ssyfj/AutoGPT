import os

def load_file(file_path,file_name):
    with open(os.path.join(file_path, file_name), 'r',encoding='utf-8') as file:
        return file.read()