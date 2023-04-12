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
RUN rm -rf /var/lib/apt/lists/*
# Init docker workdir:
WORKDIR /app
# Copy local files to workdir:
COPY ffserver_install.sh run_rtsp_multiport_streamer.sh multithread_streamer.py /app/
# Build ffserver from source:
RUN chmod +x ffserver_install.sh && ./ffserver_install.sh
# Builder succes message:
CMD ["echo 'BuildDone!"]