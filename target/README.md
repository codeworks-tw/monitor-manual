## Steps to run

### 1. Install `docker` and `docker-compose`
```shell
sudo apt update && sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
```

### 2. Check docker-compose configuraions and create .htpasswd for basic_auth in nginx
```shell
vi docker-compose.yml

# generate an Apache MD5-encoded password hash for use in .htpasswd files
openssl passwd -apr1

# replace username and password with yours and create .htpasswd
echo '(username):(password generated)' > .htpasswd
```

### 3.Run `docker-compose` to start all containers
```shell
docker-compose up -d
```