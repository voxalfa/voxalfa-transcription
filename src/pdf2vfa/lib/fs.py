import os


def write_file(name: str, buffer: str, params):
    file_path = os.path.join(params.out_dir, name)

    with open(file_path, "w+") as file:
        file.write(buffer)
