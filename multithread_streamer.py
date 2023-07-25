# Config map - different source folders ->>>> into one broadcast index.
# Striming_prefix conflict ???
#
#
#
import os
import sys
import re
import logging
import json
import shutil
import socket


import subprocess
from concurrent.futures import ThreadPoolExecutor

#########################################################
###################### Docker envs ######################
#########################################################
env_log_level = os.environ.get("LOG_LEVEL") if os.environ.get("LOG_LEVEL") else "DEBUG"

#########################################################
######################## Logger #########################
#########################################################
class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.blue + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset,
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, "%Y-%m-%d %H:%M")
        return formatter.format(record)


DOCKER_FORMAT = "%(asctime)s:%(levelname)s : %(message)s"
logger = logging.getLogger("ffserver-versatile")


# Set logging level:
if "DEBUG" == env_log_level:
    logger.setLevel(logging.DEBUG)
elif "INFO" == env_log_level:
    logger.setLevel(logging.INFO)
elif "WARN" or "WARNING" == env_log_level:
    logger.setLevel(logging.WARNING)

consoleHandler = logging.StreamHandler(sys.stdout)  # set streamhandler to stdout
consoleHandler.setFormatter(CustomFormatter(DOCKER_FORMAT))
logger.addHandler(consoleHandler)

#########################################################
#################### Config Import ######################
#########################################################

# DEV_MODE = True
DEV_MODE = False
if DEV_MODE:
    import tomli

    conf_location = "./config"
else:
    # import tomllib
    import tomli

    conf_location = "/app/config"

with open(f"{conf_location}/modules_config.toml", "rb") as config_file:
    # MODULES_CONFIG = tomllib.load(config_file)
    MODULES_CONFIG = tomli.load(config_file)

#########################################################
########### Checking allowed extention env ##############
#########################################################
parsed_allowed_extention = []
for single_ext in MODULES_CONFIG.get("general").get("allowed_vid_extentions"):
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
        logger.error(
            f"Provided 'ALLOWED_EXTENTIONS' have bad syntax. \n \
            Desired format: - ALLOWED_EXTENTIONS=.mp4,.avi,.some_ext \n \
            Trying to add dot '.' to provided extentions..."
        )
        sys.exit(1)

#########################################################


def check_provided_modules(modules_config: dict, proj_dir: str) -> map:
    """
    Check provided modules for samples existance in related directories.
    """
    try:
        for module_key in modules_config.get("modules"):
            logger.info(f"Checking {module_key} module...")

            source_dir = os.path.join(
                proj_dir,
                modules_config["general"]["vid_samples_source"],
                modules_config["modules"][module_key]["vid_samples_source_prefix"],
            )
            logger.info(f"Source directory : {source_dir}")

            workspace_dir = os.path.join(
                proj_dir,
                modules_config["general"]["vid_samples_workspace"],
                modules_config["modules"][module_key]["vid_samples_workspace_prefix"],
            )
            os.mkdir(workspace_dir)
            logger.info(f"Workspace directory : {workspace_dir}")

            module_proj_dir_content = os.listdir(source_dir)
            modules_config["modules"][module_key]["source_files"].extend(
                module_proj_dir_content
            )
        logger.debug(f"modules_config : {modules_config}")
        return modules_config
    except Exception as err:
        logger.error(err)
        logger.error(
            "Some modules missing in /video_samples/{module_name}\n\n \
            ! Please remove module from modules_config.toml or add samples into missing directory !"
        )
        sys.exit(1)


def shift_sample(modules_cfg: dict, proj_dir: str) -> map:
    """
    Shift video samples if needed, othervise mcopy it to workspace
    """
    try:
        shifted_samples = []
        for module in modules_cfg["modules"]:
            for input_file in modules_cfg["modules"][module]["source_files"]:
                logger.info(f"Processing {input_file}...")
                i = 1

                source_name = modules_cfg["general"]["vid_samples_source"]
                workspace_name = modules_cfg["general"]["vid_samples_workspace"]

                shift_interval = modules_cfg["modules"][module]["shift_interval"]
                vid_samples_source_prefix = modules_cfg["modules"][module][
                    "vid_samples_source_prefix"
                ]
                vid_samples_workspace_prefix = modules_cfg["modules"][module][
                    "vid_samples_workspace_prefix"
                ]
                output_fps = modules_cfg["modules"][module]["frame_rate"]
                skip_resize = modules_cfg["modules"][module]["skip_resize"]
                output_resolution = modules_cfg["modules"][module]["resize_resolution"]

                while i <= modules_cfg["modules"][module]["copies_number"]:
                    output_file_naming = f"{input_file.split('.')[0]}_{i}.mp4"
                    logger.debug(f"output_file_naming == {output_file_naming}")
                    i += 1

                    if skip_resize:
                        ffmpeg_command = [
                            "ffmpeg",
                            "-y",  # overrites if file exist
                            "-i",  # input file key
                            f"{proj_dir}/{source_name}/{vid_samples_source_prefix}/{input_file}",  # input file path
                            "-ss",  # shift key
                            f"{shift_interval*i}",  # shift amount
                            "-an",  # deletes audio
                            "-r",  # select desired fps
                            f"{output_fps}",  # select desired fps
                            "-c:v",  # quick copy without any transcoding or re-encoding
                            "copy",  # quick copy without any transcoding or re-encoding
                            f"{proj_dir}/{workspace_name}/{vid_samples_workspace_prefix}/{output_file_naming}",  # output destenation/file.name
                        ]
                    else:
                        ffmpeg_command = [
                            "ffmpeg",
                            "-y",  # overrites if file exist
                            "-i",  # input file key
                            f"{proj_dir}/{source_name}/{vid_samples_source_prefix}/{input_file}",  # input file path
                            "-ss",  # shift key
                            f"{shift_interval*i}",  # shift amount
                            "-an",  # deletes audio
                            "-vf",  # resize key
                            f"scale={output_resolution}",  # resize scale
                            "-r",  # select desired fps
                            f"{output_fps}",  # select desired fps
                            "-vcodec",  # select codec
                            "libx264",  # H.264
                            f"{proj_dir}/{workspace_name}/{vid_samples_workspace_prefix}/{output_file_naming}",  # output destenation/file.name
                        ]
                        logger.warning(ffmpeg_command)

                    with subprocess.Popen(
                        ffmpeg_command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        encoding="utf-8",
                        errors="replace",
                    ) as proc:
                        add_current_sample = True

                        while True:
                            realtime_output = proc.stdout.readline()

                            if realtime_output == "" and proc.poll() is not None:
                                break

                            if realtime_output:
                                if re.search("frame=", realtime_output):
                                    logger.info(realtime_output.strip())
                                elif re.search(input_file, realtime_output):
                                    logger.info(realtime_output.strip())

                                elif re.search("Invalid", realtime_output):
                                    logger.error(realtime_output.strip())
                                    add_current_sample = False
                                elif re.search("error", realtime_output):
                                    logger.error(realtime_output.strip())
                                    add_current_sample = False
                                elif re.search("contradictionary", realtime_output):
                                    logger.error(realtime_output.strip())
                                    add_current_sample = False
                                else:
                                    logger.debug(realtime_output.strip())

                        # Add only verified samples:
                        if add_current_sample:
                            shifted_samples.append(
                                f"{proj_dir}/{workspace_name}/{vid_samples_workspace_prefix}/{output_file_naming}"
                            )
                            modules_cfg.get("modules").get(module)[
                                "shifted_files"
                            ].append(
                                f"{proj_dir}/{workspace_name}/{output_file_naming}"
                            )

        logger.info(f"Shifted files list: {shifted_samples}")
        logger.debug(f"New module_cfg: {modules_cfg}")
        return modules_cfg
    except Exception as err:
        logger.error(err)
        sys.exit(1)


def port_in_use(port: int):
    """Checks provided port number for availability"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        port_busy = bool(sock.connect_ex(("localhost", int(port))) == 0)
        if port_busy:
            logger.info(f"Port {port} is in Use. Skipping...")
        else:
            logger.info(f"Port {port} is Free. Applying...")
        return port_busy


def calculate_max_bandwidth(modules_cfg: dict, each_max_bandwidth: int = 5000):
    """
    Calculating max_bandwidth value for ffserver:
    """
    all_samples = []

    for _, module_value in modules_cfg["modules"].items():
        all_samples.extend(module_value["shifted_files"])

    feed_num = len(all_samples)
    max_bandwidth = each_max_bandwidth * feed_num
    return max_bandwidth


def create_ffserver_conf(modules_cfg: dict, proj_dir: str):
    """
    Creates config for ffserver, from which broadcast will be.
    """
    config_name = "ffserver.conf"
    conf_inbound_ports = list(modules_cfg["general"]["internal_port_range"])
    conf_outbound_ports = list(modules_cfg["general"]["external_port_range"])

    free_outbound_port: int
    free_inboung_port: int

    # Locate free inbound port:
    for i_port in conf_inbound_ports:
        if not port_in_use(i_port):
            free_inboung_port = i_port
            break
    # Locate free outboud port:
    for o_port in conf_outbound_ports:
        if not port_in_use(o_port):
            free_outbound_port = o_port
            break

    # Calculating max_bandwidth value for ffserver:
    max_bandwidth = calculate_max_bandwidth(modules_cfg)

    ffserver_base_conf = f"""\
HTTPPort {free_inboung_port}
HTTPBindAddress 0.0.0.0
MaxHTTPConnections 2000
MaxClients 1000
MaxBandwidth {max_bandwidth} 
CustomLog -

RTSPPort {free_outbound_port}
RTSPBindAddress 0.0.0.0
"""

    ffserver_streams_conf = """"""
    ffserver_streams_patern = """
<Stream str_{stream_prefix}_{stream_num}>
    Format rtp
    File "{workspace}/{feed_name}"
</Stream>
"""

    ffserver_status_conf = """
<Stream status.html>
    Format status
    ACL allow 0.0.0.0 255.255.255.255
</Stream>"""

    for module_key, module_value in modules_cfg["modules"].items():
        broadcast_num = 0
        for vid_file_path in module_value["shifted_files"]:
            # Only file name:
            vid_file_naming_ext = os.path.basename(vid_file_path)
            vid_file_naming = broadcast_num
            broadcast_num += 1

            ffserver_streams_conf += ffserver_streams_patern.format(
                feed_name=vid_file_naming_ext,
                stream_prefix=module_value["stream_url_prefix"],
                stream_num=vid_file_naming,
                workspace=os.path.join(
                    proj_dir,
                    modules_cfg["general"]["vid_samples_workspace"],
                    module_value["vid_samples_workspace_prefix"],
                ),
            )

    config_content = """"""
    config_content = ffserver_base_conf + ffserver_streams_conf + ffserver_status_conf

    with open(
        os.path.join(
            proj_dir, modules_cfg["general"]["vid_samples_workspace"], config_name
        ),
        "w",
    ) as ffs_conf_file:
        ffs_conf_file.write(config_content)

    return config_name, config_content, free_outbound_port


def main(proj_dir: str, modules_config: dict = MODULES_CONFIG):
    """
    Main function
    """

    # Clean up workspace:
    os.system(f"rm -rf {proj_dir}/workspace/*")
    logger.info(f"{proj_dir}/workspace/ directory cleared")

    modules_cfg = check_provided_modules(modules_config, proj_dir)
    modules_cfg = shift_sample(modules_cfg, proj_dir)
    config_naming, config_content, config_rtsp_port = create_ffserver_conf(
        modules_cfg, proj_dir
    )

    ffserver_start_cmd = ["ffserver", "-f", config_naming]

    broadcast_ip = subprocess.check_output(
        "hostname -I | awk '{print $1}'", shell=True, text=True
    ).strip()
    broadcast_url = f"rtsp://{broadcast_ip}:{config_rtsp_port}/"

    logger.info(
        f""" ===== Broadcast parameters ===== \n
Brodcast URL: {broadcast_url} \n
FFserver config: \n
{config_content} \n\n"""
    )

    logger.warning(
        """!!! Please make sure there are no WARNINGS/ERRORS below this message !!!"""
    )
    logger.info("RTSP URLS:")
    with open(
        os.path.join(
            proj_dir, modules_cfg["general"]["vid_samples_workspace"], config_naming
        ),
        "r",
    ) as conf_file:
        for line in conf_file:
            if path_mObj := re.search("(\/.*\.mp4)", line):
                logger.info(f"Source File    : {path_mObj[0]}")
            if prefix_mObj := re.search("(str_.*\d+)", line):
                logger.info(f" Broadcast URL : {broadcast_url}{prefix_mObj[0]}")

    with subprocess.Popen(
        ffserver_start_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
        cwd=os.path.join(proj_dir, modules_cfg["general"]["vid_samples_workspace"]),
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
                elif re.search("started", realtime_output):
                    logger.info(realtime_output.strip())
                elif re.search(
                    "Invalid data found when processing input", realtime_output
                ):
                    logger.warning(realtime_output.strip())
                elif re.search("Could not open", realtime_output):
                    logger.error(realtime_output.strip())
                elif re.search("[TEARDOWN]", realtime_output):
                    logger.debug(realtime_output.strip())
                elif re.search("unspecified pixel format", realtime_output):
                    logger.error(realtime_output.strip())


if __name__ == "__main__":
    if DEV_MODE:
        project_location = (
            MODULES_CONFIG.get("general").get("developer").get("project_dir")
        )
        logger.info(f"Current project_location is {project_location}")
    else:
        project_location = (
            MODULES_CONFIG.get("general").get("docker").get("project_dir")
        )
        logger.info(f"Current project_location is {project_location}")

    main(proj_dir=project_location, modules_config=MODULES_CONFIG)
