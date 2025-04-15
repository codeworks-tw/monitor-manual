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

### 3. Grant execution permission for grafana plugin and run `docker-compose ` to start all containers
```shell
chmod +x config/grafana/plugins/mahendrapaipuri-dashboardreporter-app/gpx_dashboardreporter-app_linux_amd64
chmod +x config/grafana/plugins/mahendrapaipuri-dashboardreporter-app/gpx_dashboardreporter-app_linux_amd
docker-compose up -d
```

## Trivial Commands
```shell
# reload prometheus configuration
docker exec prometheus kill -HUP 1
# start a test container
docker run --rm -d --name mem_test_container -m 256m --memory-swap 256m alpine sleep 300
# do stress test
stress --vm 1 --vm-bytes 450M --timeout 5m
```