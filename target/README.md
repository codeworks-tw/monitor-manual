## Steps to run monitor target

This guide will help you set up a monitoring target on your Ubuntu machine using Docker.

### 1. Install `Docker` and `Docker Compose`

Follow the official Docker installation guide for Ubuntu:
[docker official installation steps](https://docs.docker.com/engine/install/ubuntu)

```shell
# Add Docker's official GPG key
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

# Install Docker and Docker Compose
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 2. Configure Basic Authentication

1. Review the Docker Compose configuration:
   ```shell
   vi docker-compose.yml
   ```

2. Set up basic authentication by creating a `.htpasswd` file:
   ```shell
   # Replace 'username' and 'password' with your desired credentials
   echo "(username):$(echo -n '(password)' | openssl passwd -apr1 -stdin)" > .htpasswd
   ```

### 3. Start the Containers

Launch all containers using Docker Compose:
```shell
docker compose up -d
```

### 4. Verify Port Access

Ensure that port 8080 is accessible on your machine. You may need to:
- Configure your firewall to allow traffic on port 8080
- Ensure the port is not being used by other services

### 5. Update prometheus.yml target list on host machine

1. Locate the prometheus.yml configuration file:
   ```shell
   vi prometheus.yml
   ```

2. Add your target endpoints to the `scrape_configs` section. Example:
   ```yaml
   scrape_configs:
    - job_name: 'node-status'
      ...
      static_configs:
        - targets: ['your-target-ip:8080']
          labels:
            group: 'your-group-name'
            source: 'node'
      ...
    - job_name: 'docker-status'
      static_configs:
        - targets: ['your-target-ip:8080']
        labels:
            group: 'your-group-name'
            source: 'docker'
      ...
   ```

3. Restart the Prometheus container to apply changes:
   ```shell
   docker compose restart prometheus
   # or
   docker exec prometheus kill -HUP 1
   ```

## Additional Information
- Basic authentication will be required to access the monitoring interface
