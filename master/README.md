## Steps to run

### 1. Install `docker` and `docker compose`

[docker official installation steps](https://docs.docker.com/engine/install/ubuntu)

```shell
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 2. Create prometheus config from template and check the configuraions
```shell
cp config/prometheus.template.yml config/prometheus.yml
vi config/prometheus.yml

# Compose file for deploying only Grafana and Prometheus
vi docker-compose-light.yml

# Compose file for deploying only renderer and Chrome
vi docker-compose-renderer.yml

# Full deployment of all services — suitable for local testing or machines with sufficient memory (16G)
vi docker-compose.yml
```

### 2.1 Generate SSL cert (optional)

```shell
docker run \
-v ./letsencrypt/cert:/etc/letsencrypt \
-ti certbot/certbot \
certonly \
  --email <email> \
  --agree-tos \
  --manual \
  --preferred-challenges dns \
  --server https://acme-v02.api.letsencrypt.org/directory \
  -d "*.yourdomain.com"
```

### 3. Grant execution permission for grafana plugin and run `docker-compose ` to start all containers
```shell
# only Grafana and Prometheus
docker compose -f docker-compose-light.yml up -d

# only renderer and Chrome
docker compose -f docker-compose-renderer.yml up -d

# Full deployment
docker compose up -d
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