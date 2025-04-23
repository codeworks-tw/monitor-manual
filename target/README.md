## Steps to run

### 1. Install `docker` and `docker-compose`
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

### 2. Check docker-compose configuraions if necessary and create .htpasswd for basic_auth in nginx
```shell
vi docker-compose.yml

# replace username and password with yours and create .htpasswd
echo "(username):$(echo -n '(password)' | openssl passwd -apr1 -stdin)" > .htpasswd
```

### 3.Run `docker-compose` to start all containers
```shell
docker compose up -d
```