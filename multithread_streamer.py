import zipfile
import argparse
import textwrap
import argparse
import shutil
import os
import re
import subprocess

# Requirements:
import ffmpeg


####################################
### Create ArgumentParser object ###
parser = argparse.ArgumentParser(
    description="Shift provided video samples. Strim resulting samples via FFSERVER",
    formatter_class=argparse.RawTextHelpFormatter,
    add_help=False,
)

# Add the arguments:
parser.add_argument(
    "-h",
    "--help",
    action="help",
    default=argparse.SUPPRESS,
    help=textwrap.dedent(
        """\
        Show this help message and exit.
        \n"""
    ),
)
parser.add_argument(
    "-i",
    "--input_file_path",
    type=str,
    required=True,
    help=textwrap.dedent(
        """\
        Input .zip or dir path or even path to video file.
        \n"""
    ),
)
parser.add_argument(
    "-n",
    "--num_copies",
    type=int,
    default=1,
    required=False,
    help=textwrap.dedent(
        """\
        Number of copies of each provided sample.
        Default int: 1
        \n"""
    ),
)
parser.add_argument(
    "-s",
    "--shift_interval",
    type=int,
    default=5,
    required=False,
    help=textwrap.dedent(
        """\
        Same videos sample shift interval.
        Default int: 5 [sec] 
        \n"""
    ),
)
parser.add_argument(
    "-w",
    "--workspace",
    type=str,
    default="/tmp",
    required=False,
    help=textwrap.dedent(
        """\
        Can be specified relative or absolute: './path/to/workspace'.
        Default str: '/tmp/'
        \n"""
    ),
)
parser.add_argument(
    "-r",
    "--resolution",
    type=str,
    default="1920x1080",
    required=False,
    help=textwrap.dedent(
        """\
        Output samples resolution: '{width}x{height}'.
        Default str: '1920x1080'
        \n"""
    ),
)

# Parse the arguments:
args = parser.parse_args()
# Access the arguments:
args_file_path = args.input_file_path
if re.search("/$", args_file_path):
    args_file_path = re.sub("/$", "", args_file_path)
    print(f"INFO: args_file_path: {args_file_path}")
####################################


def unzip_file(
    zip_path=args_file_path, new_workspace=args.workspace
) -> tuple[list, str]:
    """
    Unzip provided .zip to args.workspace
    (Default: /tmp/ in order to save space)
    """
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_name = os.path.basename(zip_path)
        zip_ref.extractall(f"{new_workspace}/")
        print(f"INFO: {zip_path} unzipped to {new_workspace}/")
        ####### TODO:
        ####### {new_workspace}/zip_name/

        dir_content = os.listdir(f"{new_workspace}/")
        if os.path.isdir(f"{new_workspace}/{dir_content[0]}"):
            new_workspace = f"{new_workspace}/{dir_content[0]}"
            dir_content = os.listdir(f"{new_workspace}/")
        else:
            new_workspace = f"{new_workspace}"
    return dir_content, new_workspace


def read_dir_content(
    dir_path=args_file_path, workspace=args.workspace
) -> tuple[list, str]:
    """
    Return provided directory content. Copy to args.workspace
    (Default: /tmp/ in order to save space)
    """
    dir_name = os.path.basename(dir_path)
    dir_content = os.listdir(dir_path)

    if workspace == dir_name:
        print(
            f"ERROR: workspace cant be equal to source directory! (workspace:{workspace}, source_dir:{dir_name})"
        )
    elif workspace == "./":
        new_workspace = "."
        shutil.copytree(dir_path, f"{workspace}/", dirs_exist_ok=True)
        print(f"INFO: entire {dir_path} directory copied to {new_workspace}/")
    else:
        new_workspace = f"{workspace}/{dir_name}"
        shutil.copytree(dir_path, f"{workspace}/{dir_name}", dirs_exist_ok=True)
        print(f"INFO: entire {dir_path} directory copied to {new_workspace}/")

    print(new_workspace)
    for file in dir_content:
        if dir_content.index(file) == len(dir_content) - 1:
            print(f"└── {file}")
        else:
            print(f"├── {file}")
    return dir_content, new_workspace


def shift_sample(
    input_files: list,
    workspace: str,
    num_copies=args.num_copies,
    shift_interval=args.shift_interval,
    output_resolution=args.resolution,
    orig_file_path=args_file_path,
):
    """
    Create output video samples from input_files list, according to copies_num.
    Default output_resolution is FullHD(1920x1080), can be changed with '-r' input key.trim
    """
    print(f"INFO: Input files: {input_files}")
    print(f"INFO: Number of copies: {num_copies}")
    for input_file in input_files:
        print(f"INFO: Processing {input_file}...")
        i = 1
        while i <= num_copies:
            output_file_naming = f"{input_file.split('.')[0]}_{i}.mp4"
            i += 1
            proc = subprocess.Popen(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    f"{workspace}/{input_file}",
                    "-ss",
                    f"{shift_interval*i}",
                    "-vf",
                    f"scale={output_resolution}",
                    "-c:a",
                    "copy",
                    f"{workspace}/{output_file_naming}",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding="utf-8",
                errors="replace",
            )
            while True:
                realtime_output = proc.stdout.readline()

                if realtime_output == "" and proc.poll() is not None:
                    print("", flush=True)
                    break

                if realtime_output:
                    if re.search("frame=", realtime_output):
                        print(f"INFO: {realtime_output.strip()}", flush=True, end="\r")

                    elif re.search(input_file, realtime_output):
                        print(f"WARN: {realtime_output.strip()}", flush=True, end="\r")


def main():
    """Main func info here"""
    if os.path.isdir(args.input_file_path):
        dir_content, workspace = read_dir_content()
    elif os.path.splitext(os.path.basename(args.input_file_path))[1] == ".zip":
        dir_content, workspace = unzip_file()
    else:
        dir_content = [os.path.basename(args.input_file_path)]
        workspace = args.workspace
        # Copy single file to workspace:
        if args.workspace != "./":
            shutil.copy(args.input_file_path, args.workspace)
            print(f"INFO: {args.input_file_path} file copied to {args.workspace}/")
        else:
            print(f"INFO: working in currect directory: './'")

    shift_sample(dir_content, workspace)


if __name__ == "__main__":
    main()


# HTTPPort 8100
# HTTPBindAddress 0.0.0.0
# MaxHTTPConnections 2000
# MaxClients 1000
# MaxBandwidth 5000000
# CustomLog -

# RTSPPort 7660
# RTSPBindAddress 0.0.0.0

# <Stream test>
#     Format rtp
#     File "tashir2K.mp4"
# </Stream>
###
