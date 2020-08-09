FROM ubuntu:latest

WORKDIR /usr/src/app

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update -y && apt-get upgrade -y
RUN apt-get install -y python3-pip libopencv-dev python3-opencv
RUN apt-get install -y pyqt5-dev-tools python3-pyqt5 qttools5-dev-tools libgl1
RUN apt-get install -y mysql-server
RUN service mysql start

COPY requirements.txt /usr/src/app
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /usr/src/app