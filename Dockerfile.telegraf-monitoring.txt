FROM telegraf

ENV INSTALL_KEY=379CE192D401AB61
ENV DEB_DISTRO=bionic

RUN apt update && apt install -y \
    gnupg1 apt-transport-https dirmngr \
    && rm -rf /var/lib/apt/lists/*

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys $INSTALL_KEY
RUN echo "deb https://ookla.bintray.com/debian ${DEB_DISTRO} main" >> /etc/apt/sources.list.d/speedtest.list
RUN apt update && apt install -y \
    speedtest \
    && rm -rf /var/lib/apt/lists/*

RUN speedtest --accept-gdpr --accept-license
