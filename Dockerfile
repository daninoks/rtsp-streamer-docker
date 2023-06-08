FROM jrottenberg/ffmpeg:5.1.2-ubuntu2004 AS FFmpeg
FROM ubuntu:20.04

# Copy ffmpeg to webservice ubuntu
COPY --from=FFmpeg / /
ENV DEBIAN_FRONTEND=noninteractive

# Update system and install dependacies for Pyrhon3.10:
RUN rm -rf /var/lib/apt/lists/*
RUN apt-get update -y && apt-get --fix-broken install -y
RUN apt-get install apt-utils software-properties-common python3.10 -y && \
    python3 --version

# Build ffserver from source:
RUN apt-get install git curl wget ffmpeg make gcc yasm screen net-tools -y
RUN git clone https://git.ffmpeg.org/ffmpeg.git ffmpeg
RUN cd ffmpeg && \
    git checkout 2ca65fc7b74444edd51d5803a2c1e05a801a6023 && \
    ./configure && \
    make -j4 && \
    mv ffserver /bin/ffserver

# Empty apt list:
RUN rm -rf /var/lib/apt/lists/*

# Init docker workdir:
WORKDIR /app

# Copy local files to workdir:
COPY multithread_streamer.py /app/
RUN chmod -R +x /app/

# Command on launch that can be overwriten:
CMD [ "rm", "-rf", "/app/workspace/*" ]
# Command on launch that can't be overwriten:
ENTRYPOINT [ "python3", "/app/multithread_streamer.py" ]
