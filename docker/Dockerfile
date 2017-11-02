FROM debian:stretch

RUN apt-get update -y && \
DEBIAN_FRONTEND=noninteractive apt-get install -qy htop procps golang python3-venv python3-dev libpq5 build-essential curl sudo make cpio bzip2 vim less git && \
apt-get clean

CMD ["/bin/bash"]
