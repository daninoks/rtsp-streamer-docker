# rtsp-streamer-docker

## Usage:

1. Create docker-compose.yml with environments provided below.
2. Put videos sample into {BASE_DIR}/video_samples/ (can be: single/multiple file(s) / '.zip' or '.tar.gz' file with samples)
3. Pull daninoks/ffserver-versatile:v1 docker image, or just start the docker container with `docker-compose up`
4. RTSP links will be provided in docker logs.

## Environment vars:

> LOG_LEVEL {DEBUG, WARNING, INFO}
>
> - Logging level. Select 'DEBUG' for more detailed output.

> INERNAL_PORTS {'1,2,3,...', '5000,5002,...'}
>
> - List from which ports will be checked one by one, if any of is free - it will be used as HTTP port, for video samples input.

> EXTERNAL_PORTS {'4,5,6,...', '5001,5003,...'}
>
> - List from which ports will be checked one by one, if any of is free - it will be used as RTSP port, for video samples output.

> NUM_COPIES {1}
>
> - Represent amount of copies of each provided sample to be broadcasted.

> SHIFT_INTERVAL {5} [seconds]
>
> - Time interval on which each video start point will be shifted.

> FRAME_RATE {30} [fps]
>
> - Disired frame reate of output samples.

> EACH_STREAM_MAX_BANDWIDTH {aproxymatly 8000 for one FHD sample}
>
> - This the maximum amount of kbit/sec that you are prepared to consume when streaming to clients.

> OUTPUT_RESOLUTION {1920x1080}
>
> - Resolution of output stream to broadcast. Any resolution and demention can be provided.

> ALLOWED_EXTENTIONS {mp4}
>
> - Selected alloved formats.
>   **!!! Stable only with .mp4 !!!**

> - WORKERS_NUM {32}
> - Workers amount. Should be >= number of streams[video_samples_num*copies_num] and <= number of threads available on your work station.

> **DEPRICATED:**
>
> - WORKSPACE {str: default workspace for ffmpeg/ffserver operations}
> - SOURCE_PATH {str: default input source directory}

### docker-compose.yml with default fields and formatting:

## v1 - v1.2 :

```
version: "3.0"
services:
  postgres:
    image: daninoks/ffserver-versatile:v1
    container_name: ffserver-versatile
    network_mode: "host"
    restart: always
    volumes:
      - ./video_samples:/app/video_samples
      - ./workspace:/app/workspace
    environment:
      - LOG_LEVEL=DEBUG
      - NUM_COPIES=1
      - SHIFT_INTERVAL=0
      - SKIP_RESIZE=True
      - RESIZE_RESOLUTION=1920x1080
      - ALLOWED_EXTENTIONS=mp4
      - WORKSPACE=/app/workspace
      - SOURCE_PATH=/app/video_samples
      - WORKERS_NUM_LIMIT=32
    command: sh -c "python3 /app/multithread_streamer.py"
```

## v1.3 :

```
version: "3.0"
services:
  postgres:
    image: f
    container_name: ffserver-versatile:v1.3
    network_mode: "host"
    # restart: always
    volumes:
      - ./video_samples:/app/video_samples
      - ./workspace:/app/workspace
    environment:
      - LOG_LEVEL=DEBUG
      - INERNAL_PORTS=40000,30000,30001,30002
      - EXTERNAL_PORTS=41000,31000,31001,31002
      - NUM_COPIES=1
      - SHIFT_INTERVAL=0
      - FRAME_RATE=30
      - EACH_STREAM_MAX_BANDWIDTH=10000
      - SKIP_RESIZE=False
      - RESIZE_RESOLUTION=1920x1080
      - ALLOWED_EXTENTIONS=.mp4
      - WORKERS_NUM_LIMIT=32
```

## Changelog:

### ffserver-versatile:v1.3.1

- Now streams naming is static instead of dynamic in 1.3

`rtsp://192.123.123.123:41000/str_<vide_file_naming>_<copy_index>  >>>  rtsp://192.123.123.123:41000/str_<stream_index>`

### ffserver-versatile:v1.3

- FFserver structure changed: now container launching single FFserver instance with multiple streams.
- Feed naming replaced old 'test' feed name. Current connection pattern: 'rtsp://{HOST}:{EXTERNAL*PORT}/str*{VIDEO_FILE_BASE_NAME}'
- INERNAL_PORTS and EXTERNAL_PORTS check range can be changed.
- FRAME_RATE added. Changed the output files frame rate.
- EACH_STREAM_MAX_BANDWIDTH added. Allow to change max bandwidth for each streaming feed.
- '.zip' and '.tar.gz' extantions now supported. (.mp4 still best choice for input video samples)
- WORKSPACE and WORKSPACE environments removed
