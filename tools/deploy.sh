# !/bin/bash

# docker가 없다면, docker 설치
if ! type docker > /dev/null
then
  echo "docker does not exist"
  echo "Start installing docker"
  sudo apt-get update
  sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
  sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
  sudo apt update
  apt-cache policy docker-ce
  sudo apt install -y docker-ce
fi


IMAGE_NAME="dojini/minesweeper:latest"
CONTAINER_NAME="minesweeper"
ENV_FILE_PATH=".env"
VOLUME_MOUNT_PATH="/var/lib/gamulpung"

# 컨테이너가 존재하는지 확인
if sudo docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"
then
  sudo docker rm -f $CONTAINER_NAME
fi 

if sudo docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "^${IMAGE_NAME}$"
then
  sudo docker rmi $IMAGE_NAME
fi

sudo docker run -it -d 
  -p 80:8000 \
  -v ".:$VOLUME_MOUNT_PATH" \
  --env-file $ENV_FILE_PATH \
  --name $CONTAINER_NAME \ 
  $IMAGE_NAME
