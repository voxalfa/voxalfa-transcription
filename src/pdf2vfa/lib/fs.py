import os


def write_file(name: str, buffer: str, out_dir: str):
    file_path = os.path.join(out_dir, name)

    with open(file_path, "w+") as file:
        file.write(buffer)
