# rtsp-streamer-docker

## Usage:

1. Create docker-compose.yml with environments provided below.
2. Put videos sample into {BASE_DIR}/video_samples/ { can be: single/multiple file(s) / directory with samples / .zip file with samples }
3. Pull daninoks/ffserver-versatile:v1 docker image, or just start the docker container with `docker-compose up`
4. RTSP links will be provided in docker logs.

### Environment vars:

> - LOG_LEVEL {DEBUG, WARNING, INFO}
> - NUM_COPIES {int: represent amount of copies of each provided sample to be streamed}
> - SHIFT_INTERVAL {int: time interval on which each video start point will be shifted}
> - OUTPUT_RESOLUTION {str: any resolution and demention can be provided}
> - ALLOWED_EXTENTIONS {str: [mp4] stable only with mp4}
> - WORKSPACE {str: default workspace for ffmpeg/ffserver operations}
> - SOURCE_PATH {str: default input source directory}
> - WORKERS_NUM {int: Workers amount. Should be >= number of streams[video_samples_num*copies_num] and <= number of threads available on your work station.}

### docker-compose.yml with default fields and formatting:

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
      # - ./workspace:/app/workspace
    environment:
      - LOG_LEVEL=DEBUG
      - NUM_COPIES=5
      - SHIFT_INTERVAL=5
      - OUTPUT_RESOLUTION=1920x1080
      - ALLOWED_EXTENTIONS=mp4
      - WORKSPACE=/app/workspace
      - SOURCE_PATH=/app/video_samples
      - WORKERS_NUM=8
    command: sh -c "python3 /app/multithread_streamer.py"
```
