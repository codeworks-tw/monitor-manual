## Steps to run

### 1. Install `docker` and `docker-compose`
```shell
sudo apt update && sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
```

### 2. Create prometheus config from template and check the configuraions
```shell
cp config/prometheus.template.yml config/prometheus.yml
vi config/prometheus.yml
# check docker-compose config as well
vi docker-compose.yml
```

### 3. Create the docker `network` defined in file and run `docker-compose `
```shell
docker network create monitor-network
docker-compose up -d
```

