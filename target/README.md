## Steps to run

### 1. Install `docker` and `docker-compose`
```shell
sudo apt update && sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
```

### 2. Check docker-compose configuraions
```shell
vi docker-compose.yml
```

### 3. Create the docker `network` defined in file and run `docker-compose`
```shell
docker network create monitor-target-network
docker-compose up -d
```

