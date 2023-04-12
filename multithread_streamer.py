import zipfile
import shutil
import os
import re
import subprocess
import time
import logging
from concurrent.futures import ThreadPoolExecutor

#########################################################
###################### Docker envs ######################
env_num_copies = os.environ.get("NUM_COPIES") if os.environ.get("NUM_COPIES") else 1
env_shift_interval = (
    os.environ.get("SHIFT_INTERVAL") if os.environ.get("SHIFT_INTERVAL") else 5
)
env_output_resolution = (
    os.environ.get("OUTPUT_RESOLUTION")
    if os.environ.get("OUTPUT_RESOLUTION")
    else "1920x1080"
)
env_allowed_extentions = (
    os.environ.get("ALLOWED_EXTENTIONS")
    if os.environ.get("ALLOWED_EXTENTIONS")
    else "mp4"
)
env_workspace = (
    os.environ.get("WORKSPACE") if os.environ.get("WORKSPACE") else "/app/workspace"
)
env_source_path = (
    os.environ.get("SOURCE_PATH")
    if os.environ.get("SOURCE_PATH")
    else "/app/video_samples"
)
env_workers_num = os.environ.get("WORKERS_NUM") if os.environ.get("WORKERS_NUM") else 16
#########################################################
######################## Logger #########################
FORMAT = "{asctime} : {levelname} : {message}"
# "%(asctime)s %(clientip)-15s %(user)-8s %(message)s"
logging.basicConfig(
    filename="ffserver-versatile.log",
    filemode="w",
    level=logging.DEBUG,
    format=FORMAT,
    datefmt="%Y-%m-%d %I:%M:%S%p",
)
logger = logging.getLogger("ffserver-versatile")
#########################################################


def unzip_file(zip_path=env_source_path, workspace=env_workspace) -> list:
    """
    Unzip provided .zip to workspace
    (Default: /tmp/ in order to save space)
    """
    samples_content = os.listdir(f"{zip_path}/")
    for sample in samples_content:
        with zipfile.ZipFile(f"{zip_path}/{sample}", "r") as zip_ref:
            zip_ref.extractall(f"{workspace}/")
            logger.info(f"{zip_path}/{sample} unzipped to {workspace}/")

            ws_content = os.listdir(f"{workspace}/")
            for ws_sample in ws_content:
                if os.path.isdir(f"{workspace}/{ws_sample}"):
                    shutil.copytree(
                        f"{workspace}/{ws_sample}", workspace, dirs_exist_ok=True
                    )
                    logger.info(
                        f"{workspace}/{ws_sample} content copied to {workspace}/"
                    )
                    shutil.rmtree(f"{workspace}/{ws_sample}")
                    logger.info(f"{workspace}/{ws_sample} cleaned")
    return ws_content


def read_dir_content(source_dir_path=env_source_path, workspace=env_workspace) -> list:
    """
    Return provided directory content. Copy to workspace
    (Default: /tmp/ in order to save space)
    """
    source_dir_name = os.path.basename(source_dir_path)
    source_dir_content = os.listdir(source_dir_path)

    if workspace == source_dir_name:
        logger.warning(
            f"Workspace can't be equal to source directory! (workspace:{workspace}, source_dir:{source_dir_name})"
        )
        workspace = "/app/workspace"
        shutil.copytree(source_dir_path, f"{workspace}/", dirs_exist_ok=True)
    elif workspace == "./":
        workspace = "/app/workspace"
        logger.warning(f"'./' selected, the workspace is '/app/workspace'")
        shutil.copytree(source_dir_path, f"{workspace}/", dirs_exist_ok=True)
    else:
        shutil.copytree(
            source_dir_path, f"{workspace}/{source_dir_name}", dirs_exist_ok=True
        )
        logger.info(f"Entire {source_dir_path} directory copied to {workspace}/")

    for file in source_dir_content:
        if source_dir_content.index(file) == len(source_dir_content) - 1:
            logger.info(f"└── {file}")
        else:
            logger.info(f"├── {file}")
    return source_dir_content


def check_extention(content: list, allowed_extentions=env_allowed_extentions) -> list:
    """Check provided files extention"""
    print(f"INFO: files list before check: {content}")
    valid_list = []
    for item in content:
        if item.split(".")[-1] in allowed_extentions:
            valid_list.append(item)
        else:
            logger.warning(
                f"{item} not in 'allowed_extentions':{allowed_extentions}. Item removed."
            )
    logger.info(f"Valid files list: {valid_list}")
    return valid_list


def shift_sample(
    input_files: list,
    workspace=env_workspace,
    num_copies=env_num_copies,
    shift_interval=env_shift_interval,
    output_resolution=env_output_resolution,
) -> list:
    """
    Create output video samples from input_files list, according to copies_num.
    Default output_resolution is FullHD(1920x1080), can be changed with '-r' input key.trim
    """
    logger.info(f"Input files: {input_files}")
    logger.info(f"Number of copies: {num_copies}")
    shifted_samples = []
    for input_file in input_files:
        logger.info(f"Processing {input_file}...")
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
            shifted_samples.append(output_file_naming)

            while True:
                realtime_output = proc.stdout.readline()

                if realtime_output == "" and proc.poll() is not None:
                    # print("", flush=True)
                    break

                if realtime_output:
                    if re.search("frame=", realtime_output):
                        logger.info(realtime_output.strip())
                        # print(f"INFO: {realtime_output.strip()}", flush=True, end="\r")
                    elif re.search(input_file, realtime_output):
                        logger.info(realtime_output.strip())
                        # print(f"WARN: {realtime_output.strip()}", flush=True, end="\r")

    logger.info(f"Shifted ssamples list: {shifted_samples}")
    return shifted_samples


def get_command_list(input_files: list, workspace=env_workspace) -> list:
    """Running multiple copies of ffserver"""
    command_list = []
    for item in input_files:
        logger.debug(f"Coping run_rtsp_multiport_streamer.sh to {workspace}/")
        shutil.copy("run_rtsp_multiport_streamer.sh", workspace)
        logger.info(f"Launching streamer for {item}")
        command_list.append(f"./run_rtsp_multiport_streamer.sh {item}")
    return command_list


def run_command(command: str, workspace=env_workspace) -> None:
    """Run command construction for ThreadPoolExecutor"""
    proc = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        # errors="replace",
        cwd=workspace,
    )
    while True:
        realtime_output = proc.stdout.readline()

        if realtime_output == "" and proc.poll() is not None:
            print("", flush=True)
            break

        if realtime_output:
            if re.search("Running RTSP streamer on", realtime_output):
                logger.info(realtime_output.strip())
            elif re.search("[TEARDOWN]", realtime_output):
                logger.debug(realtime_output.strip())


def main(
    source_path=env_source_path, workspace=env_workspace, workers_num=env_workers_num
) -> None:
    """Main func info here"""
    if os.path.isdir(source_path):
        dir_content = read_dir_content()
    elif os.path.splitext(os.path.basename(source_path))[1] == ".zip":
        dir_content = unzip_file()
    else:
        dir_content = os.listdir(source_path)

        for file in dir_content:
            # Copy standalone file(s) to workspace:
            if workspace == "./":
                workspace = "/app/workspace"
                shutil.copy(f"{source_path}/{file}", workspace)
                logger.warning(f"'./' selected, the workspace is '/app/workspace'")
            else:
                shutil.copy(f"{source_path}/{file}", workspace)
                logger.info(f"{source_path}/{file} file copied to {workspace}/")

    valid_files = check_extention(dir_content)
    shifted_samples = shift_sample(valid_files, workspace=workspace)
    commands = get_command_list(shifted_samples, workspace=workspace)
    logger.debug(f"Commads list : {commands}")
    # Create a thread pool worker threads
    with ThreadPoolExecutor(max_workers=workers_num) as executor:
        futures = []
        # Submit each command to the thread pool
        for cmd in commands:
            futures.append(executor.submit(run_command, cmd))
            logger.debug(f"Executing {cmd} ...")
            time.sleep(3)

        # Wait for all commands to complete
        for future in futures:
            future.result()


if __name__ == "__main__":
    main()
