import os
import sys
import shutil

import zipfile
import tarfile

import re
import time
import logging
import socket

import subprocess
from concurrent.futures import ThreadPoolExecutor

# tag bump
#########################################################
###################### Docker envs ######################
env_external_ports = (
    os.environ.get("EXTERNAL_PORTS")
    if os.environ.get("EXTERNAL_PORTS")
    else "30000,30001,30002,30003,30004,30005,30006,30007,30008,30009"
).split(",")
env_internal_ports = (
    os.environ.get("INTERNAL_PORTS")
    if os.environ.get("INTERNAL_PORTS")
    else "31000,31001,31002,31003,31004,31005,31006,31007,31008,31009"
).split(",")
env_num_copies = (
    int(os.environ.get("NUM_COPIES")) if os.environ.get("NUM_COPIES") else 1
)
env_shift_interval = (
    int(os.environ.get("SHIFT_INTERVAL")) if os.environ.get("SHIFT_INTERVAL") else 1
)
env_frame_rate = (
    int(os.environ.get("FRAME_RATE")) if os.environ.get("FRAME_RATE") else 30
)
env_each_stream_max_bandwidth = (
    int(os.environ.get("EACH_STREAM_MAX_BANDWIDTH"))
    if os.environ.get("EACH_STREAM_MAX_BANDWIDTH")
    else 10000
)
env_skip_resize = (
    bool(os.environ.get("SKIP_RESIZE")) if os.environ.get("SKIP_RESIZE") else False
)
env_resize_resolution = (
    os.environ.get("RESIZE_RESOLUTION")
    if os.environ.get("RESIZE_RESOLUTION")
    else "1920x1080"
)
env_allowed_extentions = (
    os.environ.get("ALLOWED_EXTENTIONS")
    if os.environ.get("ALLOWED_EXTENTIONS")
    else ".mp4"
).split(",")
env_workers_num_limit = (
    int(os.environ.get("WORKERS_NUM_LIMIT"))
    if os.environ.get("WORKERS_NUM_LIMIT")
    else 32
)
env_log_level = os.environ.get("LOG_LEVEL") if os.environ.get("LOG_LEVEL") else "DEBUG"
#########################################################
######################## Logger #########################
FORMAT = "%(asctime)s:%(levelname)s:%(message)s"
DOCKER_FORMAT = "%(levelname)s : %(message)s"
logging.basicConfig(
    filename="ffserver-versatile.log",
    filemode="w",
    format=FORMAT,
    datefmt="%Y-%m-%d %I:%M:%S",
)
logger = logging.getLogger("ffserver-versatile")
consoleHandler = logging.StreamHandler(sys.stdout)  # set streamhandler to stdout
consoleHandler.setFormatter(logging.Formatter(DOCKER_FORMAT))
logger.addHandler(consoleHandler)

# Set logging level:
if "DEBUG" == env_log_level:
    logger.setLevel(logging.DEBUG)
elif "INFO" == env_log_level:
    logger.setLevel(logging.INFO)
elif "WARN" or "WARNING" == env_log_level:
    logger.setLevel(logging.WARNING)
#########################################################
########### Checking allowed extention env ##############
parsed_allowed_extention = []
for single_ext in env_allowed_extentions:
    if re.search("\.\w+", single_ext):
        parsed_allowed_extention.append(single_ext)
    elif single_ext == "" or single_ext == None:
        logger.warning(
            "No 'ALLOWED_EXTENTIONS' provided, or provided list corrupted! \n \
            Desired format: - ALLOWED_EXTENTIONS=.mp4,.avi,.some_ext \n \
            For higher stability please use '.mp4' extention for input files \n \
            '.mp4' will be used during this run..."
        )
    else:
        parsed_allowed_extention.append(f".{single_ext}")
        logger.warning(
            f"Provided 'ALLOWED_EXTENTIONS' have bad syntax. \n \
            Desired format: - ALLOWED_EXTENTIONS=.mp4,.avi,.some_ext \n \
            Trying to add dot '.' to provided extentions..."
        )
        sys.exit(1)
#########################################################
###################### Dev Mode #########################
DEV_MODE = True
if DEV_MODE:
    workspace_dir = "/home/demo/automation/workspace"
    source_dir = "/home/demo/automation/video_samples"
else:
    workspace_dir = "/app/workspace"
    source_dir = "/app/video_samples"

supported_archive_ext = [".zip", ".tar.gz"]
#########################################################
#########################################################


# def clean_up(workspace=workspace_dir):
#     """Pre-run clean up"""
#     if os.path.exists(workspace):
#         p0 = subprocess.call(["rm", "-rf", f"{workspace}/*"])
#     else:
#         os.mkdir(workspace)


def check_extention(content, allowed_extentions=env_allowed_extentions):
    """Check provided files extention"""
    logger.debug(f"File(s) before check: {content}")
    valid_files = []

    if isinstance(content, list):
        for item in content:
            _, file_ext = os.path.splitext(item)
            if file_ext in allowed_extentions:
                valid_files.append(item)
                logger.info(f"Valid files list: {valid_files}")
            else:
                logger.warning(
                    f"{item} of {content} not in 'allowed_extentions':{allowed_extentions}. Item ignored."
                )
    else:
        _, file_ext = os.path.splitext(content)
        if file_ext in allowed_extentions:
            valid_files.append(content)
            logger.info(f"Valid files list: {valid_files}")
        else:
            logger.warning(
                f"{content} not in 'allowed_extentions':{allowed_extentions}. Item ignored."
            )

    return valid_files


def copy_single_file(file: str, workspace=workspace_dir):
    valid_files = []
    old_naming = file.split("/")[-1]
    new_naming = re.sub("['\(\)\s]", "", old_naming)
    file_path = os.path.dirname(file)
    valid_files.append(new_naming)
    # Check if the workspace exist:
    if not os.path.exists(workspace):
        os.mkdir(workspace)
    # Move and re-name:
    shutil.copy(
        os.path.join(file_path, old_naming),
        os.path.join(workspace, new_naming),
    )
    logger.debug(
        f"{os.path.join(file_path, old_naming)} moved to {os.path.join(workspace, new_naming)}"
    )
    return valid_files


def move_dir_content(target_dir, workspace=workspace_dir):
    """Move dir content to workspace"""
    valid_files = []
    for item in os.listdir(target_dir):
        valid_file = check_extention(item)
        if valid_file != []:
            # OLD name -> NEW name:
            old_naming = item
            new_naming = re.sub("['\(\)\s]", "", item)
            valid_files.append(new_naming)
            # Check if the workspace exist:
            if not os.path.exists(workspace):
                os.mkdir(workspace)
            # Move and re-name:
            shutil.move(
                os.path.join(target_dir, old_naming),
                os.path.join(workspace, new_naming),
            )
            logger.debug(
                f"{os.path.join(target_dir, old_naming)} moved to {os.path.join(workspace, new_naming)}"
            )
    return valid_files


def unzip_file(file_ext: str, item: str):
    """
    Unzip files;
    Delete white-spaces in file_names;
    Move files to pre-render workspace;
    """
    pre_render_list = []
    if file_ext == ".zip":
        unpacked_dirs = []

        with zipfile.ZipFile(os.path.join(source_dir, item), "r") as zip_ref:
            zip_ref.extractall(f"{source_dir}/")
            logger.info(f"{os.path.join(source_dir, item)} unzipped to {source_dir}")
            inner_files = zip_ref.namelist()
            logger.debug(f"{os.path.join(source_dir, item)} inner list : {inner_files}")

            for inner_item in inner_files:
                inner_item_splited = inner_item.split("/")[0]
                if inner_item_splited not in unpacked_dirs:
                    if os.path.isdir(os.path.join(source_dir, inner_item_splited)):
                        pre_render_list.extend(
                            move_dir_content(
                                os.path.join(source_dir, inner_item_splited)
                            )
                        )
                    unpacked_dirs.append(inner_item_splited)

    elif file_ext == ".tar.gz":
        with tarfile.open(os.path.join(source_dir, item)) as tar_ref:
            tar_ref.extractall(f"{source_dir}/")
            logger.info(f"{os.path.join(source_dir, item)} unzipped to {source_dir}")
            inner_files = zip_ref.getnames()
            logger.debug(f"{os.path.join(source_dir, item)} inner list : {inner_files}")

            for inner_item in inner_files:
                inner_item_splited = inner_item.split("/")[0]
                if inner_item_splited not in unpacked_dirs:
                    if os.path.isdir(os.path.join(source_dir, inner_item_splited)):
                        pre_render_list.extend(
                            move_dir_content(
                                os.path.join(source_dir, inner_item_splited)
                            )
                        )
                    unpacked_dirs.append(inner_item_splited)

    for dir_name in unpacked_dirs:
        shutil.rmtree(os.path.join(source_dir, dir_name))
        logger.debug(f"{os.path.join(source_dir, dir_name)} removed from {source_dir}")
    return pre_render_list


def shift_sample(
    input_files: list,
    workspace=workspace_dir,
    num_copies=env_num_copies,
    skip_resize=env_skip_resize,
    shift_interval=env_shift_interval,
    output_resolution=env_resize_resolution,
    output_framerate=env_frame_rate,
):
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
            # logger.debug(
            #     f"Copying {source_path}/{input_file} into {workspace}/{output_file_naming} with FFmpeg"
            # )
            if skip_resize:
                logger.info("RESIZE skipped...")
                ffmpeg_command = [
                    "ffmpeg",
                    "-y",  # overrites if file exist
                    "-i",  # input file key
                    f"{workspace}/{input_file}",  # input file path
                    "-ss",  # shift key
                    f"{shift_interval*i}",  # shift amount
                    "-an",  # deletes audio
                    "-r",  # select desired fps
                    f"{output_framerate}",  # select desired fps
                    "-c:v",  # quick copy without any transcoding or re-encoding
                    "copy",  # quick copy without any transcoding or re-encoding
                    f"{workspace}/{output_file_naming}",  # output destenation/file.name
                ]
            else:
                logger.info("RESIZING...")
                ffmpeg_command = [
                    "ffmpeg",
                    "-y",  # overrites if file exist
                    "-i",  # input file key
                    f"{workspace}/{input_file}",  # input file path
                    "-ss",  # shift key
                    f"{shift_interval*i}",  # shift amount
                    "-vf",  # resize key
                    f"scale={output_resolution}",  # resize scale
                    "-an",  # deletes audio
                    "-r",  # select desired fps
                    f"{output_framerate}",  # select desired fps
                    # "-vcodec",  # select codec
                    # "libx264"  # H.264
                    f"{workspace}/{output_file_naming}",  # output destenation/file.name
                ]

            # proc = subprocess.Popen(
            #     ffmpeg_command,
            #     stdout=subprocess.PIPE,
            #     stderr=subprocess.STDOUT,
            #     encoding="utf-8",
            #     errors="replace",
            # )
            with subprocess.Popen(
                ffmpeg_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding="utf-8",
                errors="replace",
            ) as proc:
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
                        else:
                            logger.debug(realtime_output.strip())

    logger.info(f"Shifted samples list: {shifted_samples}")
    return shifted_samples


##########################################################################################
##########################################################################################

# def get_command_list(input_files: list, workspace=workspace_dir):
#     """Running multiple copies of ffserver"""
#     command_list = []
#     shutil.copy("run_rtsp_multiport_streamer.sh", workspace)
#     logger.debug(f"'run_rtsp_multiport_streamer.sh' copied to {workspace}/")
#     for item in input_files:
#         command_list.append(f"./run_rtsp_multiport_streamer.sh {item}")
#     return command_list


# def run_command(command: str, workspace=workspace_dir):
#     """Run command construction for ThreadPoolExecutor"""
#     # logger.debug(f"Path for Popen : {os.getcwd()} : listdir : {os.listdir(workspace)}")
#     # new_workspace = os.chdir(f"{workspace}/")
#     # logger.debug(f"New workspace is {new_workspace}")
#     proc = subprocess.Popen(
#         command,
#         shell=True,
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE,
#         encoding="utf-8",
#         errors="replace",
#         cwd=str(workspace),
#     )
#     while True:
#         realtime_output = proc.stdout.readline()

#         if realtime_output == "" and proc.poll() is not None:
#             break

#         if realtime_output:
#             if re.search("Running RTSP streamer on", realtime_output):
#                 logger.info(realtime_output.strip())
#             elif re.search("Opening feed file", realtime_output):
#                 logger.info(realtime_output.strip())
#             elif re.search("Invalid data found when processing input", realtime_output):
#                 logger.warning(realtime_output.strip())
#             elif re.search("[TEARDOWN]", realtime_output):
#                 logger.debug(realtime_output.strip())

##########################################################################################
##########################################################################################


def port_in_use(port: int):
    """Checks provided port number for availability"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("localhost", int(port))) == 0


def create_ffserver_conf(
    videos_samples: list,
    each_max_bandwidth=env_each_stream_max_bandwidth,
    int_ports=env_internal_ports,
    ext_ports=env_external_ports,
    workspace=workspace_dir,
):
    """ """
    config_name = "ffserver.conf"
    rtsp_port = 0
    for i_port in int_ports:
        if not port_in_use(i_port):
            internal_port = i_port
            break
    for e_port in ext_ports:
        if not port_in_use(e_port):
            external_port = e_port
            rtsp_port = external_port
            break

    feed_num = len(videos_samples)
    max_bandwidth = each_max_bandwidth * feed_num

    ffserver_base_conf = f"""\
HTTPPort {internal_port}
HTTPBindAddress 0.0.0.0
MaxHTTPConnections 2000
MaxClients 1000
MaxBandwidth {max_bandwidth} 
CustomLog -

RTSPPort {external_port}
RTSPBindAddress 0.0.0.0
"""

    ffserver_streams_conf = """"""
    ffserver_streams_patern = """
<Stream str_{stream_name}>
    Format rtp
    File "{workspace}/{feed_name}"
</Stream>
"""

    ffserver_status_conf = """
<Stream status.html>
    Format status
    ACL allow 0.0.0.0 255.255.255.255
</Stream>"""

    for vid_file in videos_samples:
        # Only file name:
        vid_file_naming_ext = os.path.basename(vid_file)
        vid_file_naming = os.path.basename(vid_file).split(".")[0]

        ffserver_streams_conf += ffserver_streams_patern.format(
            feed_name=vid_file_naming_ext,
            stream_name=vid_file_naming,
            workspace=workspace,
        )

    config_content = """"""
    config_content = ffserver_base_conf + ffserver_streams_conf + ffserver_status_conf
    with open(os.path.join(workspace, config_name), "w") as ffs_conf_file:
        ffs_conf_file.write(config_content)
    return config_name, config_content, rtsp_port


# create_ffserver_conf(videos_samples, internal_ports, external_ports)


def main(
    source_dir=source_dir,
    workspace=workspace_dir,
    allowed_extentions=env_allowed_extentions,
    max_workers_num=env_workers_num_limit,
):
    """Main func info here"""
    # Make pre-run cleanup:
    # clean_up()
    try:
        # Check passed file type:
        source_dir_content = os.listdir(source_dir)
        logger.debug(f"Source directory ({source_dir}) content: {source_dir_content}")
        # Fill list of files for ffmpeg actions:
        pre_copy_list = []

        for item in source_dir_content:

            # If provided file is file:
            if os.path.isfile(os.path.join(source_dir, item)):
                logger.debug(f"{os.path.join(source_dir, item)} is file")
                file_name, file_ext = os.path.splitext(os.path.join(source_dir, item))

                # Check supported archives and unzip to source_dir:
                if file_ext in supported_archive_ext:
                    pre_copy_list.extend(unzip_file(file_ext, item))
                # Check if the file is a video file:
                elif file_ext in allowed_extentions:
                    checked_extention = check_extention(file_name + file_ext)
                    pre_copy_list.extend(copy_single_file(checked_extention[0]))

                    # pre_copy_list.extend(check_extention(file_name + file_ext))
                # Warn if non of above:
                else:
                    logger.warning(f"{file_name}{file_ext} not supported! Skipping...")

            # If provided file is directory:
            elif os.path.isdir(os.path.join(source_dir, item)):
                logger.debug(f"{os.path.join(source_dir, item)} is directory")
                shutil.copytree(
                    os.path.join(source_dir, item), source_dir, dirs_exist_ok=True
                )
                logger.debug(
                    f"Content of {os.path.join(source_dir, item)} moved to {source_dir}"
                )
                s_dir_content_tmp = os.listdir(os.path.join(source_dir, item))
                pre_copy_list.extend(check_extention(s_dir_content_tmp))

        logger.info(f"PRE-RENDER list : {pre_copy_list}")

    except Exception as err:
        logger.error(err)
        logger.error("No smaples provided. Exiting...")
        sys.exit(1)

    # Creating RTSP URLS list:
    shifted_samples = shift_sample(pre_copy_list)
    config_naming, config_content, config_rtsp_port = create_ffserver_conf(
        shifted_samples
    )
    ffserver_start_cmd = ["ffserver", "-f", config_naming]
    broadcast_ip = subprocess.check_output(
        "hostname -I | awk '{print $1}'", shell=True, text=True
    ).strip()
    broadcast_url = f"rtsp://{broadcast_ip}:{config_rtsp_port}"

    logger.info(
        f""" ===== Broadcast parameters ===== \n
Brodcast URL: {broadcast_url} \n
FFserver config: \n
{config_content} \n\n"""
    )

    broadcast_urls = """!!! Please make sure there are no WARNINGS/ERRORS below this message !!! \n\nRTSP URLS:\n"""
    for sample_full_name in shifted_samples:
        sample_name = sample_full_name.split(".")[0]
        broadcast_urls += f"{broadcast_url}/str_{sample_name}\n"
    logger.info(broadcast_urls)

    with subprocess.Popen(
        ffserver_start_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
        cwd=str(workspace),
    ) as proc:

        while True:
            realtime_output = proc.stdout.readline()

            if realtime_output == "" and proc.poll() is not None:
                break

            if realtime_output:
                if re.search("Running RTSP streamer on", realtime_output):
                    logger.info(realtime_output.strip())
                elif re.search("Opening feed file", realtime_output):
                    logger.info(realtime_output.strip())
                elif re.search(
                    "Invalid data found when processing input", realtime_output
                ):
                    logger.warning(realtime_output.strip())
                elif re.search("Could not open", realtime_output):
                    logger.error(realtime_output.strip())
                elif re.search("[TEARDOWN]", realtime_output):
                    logger.debug(realtime_output.strip())

    ##########################################################################################
    ##########################################################################################
    # commands = get_command_list(shifted_samples, workspace=workspace)

    # logger.debug(f"Commads list : {commands}")
    # # Create a thread pool worker threads
    # with ThreadPoolExecutor(max_workers=int(max_workers_num)) as executor:
    #     futures = []
    #     # Submit each command to the thread pool
    #     for cmd in commands:
    #         logger.debug(f"Executing {cmd} ...")
    #         futures.append(executor.submit(run_command, cmd))
    #         time.sleep(3)

    #     # Wait for all commands to complete
    #     for future in futures:
    #         future.result()
    ##########################################################################################
    ##########################################################################################


if __name__ == "__main__":
    main()
