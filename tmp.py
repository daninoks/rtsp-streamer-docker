# create list of aws cp commands
commands = []
for index, item in df.iterrows():
    video_name = os.path.basename(item["path"])
    if not os.path.exists(os.path.join(LOCAL_DOWNLOAD_PATH, video_name)):
        commands.append(
            f"aws s3 cp {S3_PATH}{str(item['path'])} {LOCAL_DOWNLOAD_PATH}"
        )  # --profile scylla


def run_command(command):
    # Execute command using subprocess
    proc = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = proc.communicate()
    # Print output and error messages
    print(stdout.decode())
    with open(
        "/home/scylla/nosir/dataset/engine_test_NEW/download_info.txt", "a"
    ) as info_f:
        info_f.write(f"{stdout.decode()}\n")

    if stderr.decode():
        print(stderr.decode())
        with open(
            "/home/scylla/nosir/dataset/engine_test_NEW/download_info_error.txt", "a"
        ) as info_er:
            info_er.write(f"{stderr.decode()}\n")


# Create a thread pool worker threads
with ThreadPoolExecutor(max_workers=40) as executor:
    # Submit each command to the thread pool
    futures = [executor.submit(run_command, cmd) for cmd in commands]

    # Wait for all commands to complete
    for future in futures:
        future.result()
