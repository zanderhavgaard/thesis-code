resource "digitalocean_droplet" "db-server" {
  image = "ubuntu-20-04-x64"
  name = "db-server"
  region = "fra1"
  size = "s-2vcpu-2gb"
  private_networking = true
  ssh_keys = [var.db_ssh_fingerprint, var.client_ssh_fingerprint, var.orch_ssh_fingerprint]
}

resource "random_password" "password" {
  length = 50
}

resource "null_resource" "root-provisioner" {
  connection {
    user = "root"
    host = digitalocean_droplet.db-server.ipv4_address
    type = "ssh"
    private_key = file(var.db_pvt_key)
    timeout = "2m"
  }

  provisioner "remote-exec" {
    inline = [
      # wait for cloud-init to finish
      "while [ ! -f /var/lib/cloud/instance/boot-finished ]; do echo 'Waiting for cloud-init...'; sleep 1; done",

      # configure firewall
      "ufw default allow outgoing",
      "ufw default deny incoming",
      "ufw allow ssh",
      "ufw allow 7890"
      "ufw --force enable",
      "systemctl enable ufw",

      # install stuff
      "apt-get update -q",
      "apt-get upgrade -qq",
      "apt-get install -qq neovim figlet unzip git docker-compose",

      # enbale docker
      "systemctl enbale --now docker",
      "sudo usermod -aG docker ubuntu",

      # setup non root user
      "useradd --create-home --shell /bin/bash --groups docker ${var.username}",
      "echo \"${var.username}:${random_password.password.result}\" | chpasswd",
      "mkdir /home/ubuntu/.ssh",
      "cp /root/.ssh/* /home/ubuntu/.ssh/",
      # uncomment to disallow root access
      # "rm -rf /root/.ssh",
      "echo export DB_SQL_USER=${var.DB_SQL_USER} >> /home/ubuntu/db.env",
      "echo export DB_SQL_PASS=${var.DB_SQL_PASS} >> /home/ubuntu/db.env",
      "echo export DB_SQL_ROOT_PASS=${var.DB_SQL_ROOT_PASS} >> /home/ubuntu/db.env",
      "echo \"figlet 'db-server'\" >> /home/ubuntu/.bashrc",
      "echo 'alias mysql_connect=\"docker run --rm -it --network host mysql:5.7 mysql -u\$DB_SQL_USER -p\$DB_SQL_PASS -h127.0.0.1 -P3306 Benchmarks\"' >> /home/ubuntu/.bashrc",
      "echo 'alias mysql_query=\"docker run --rm -it --network host mysql:5.7 mysql -u\$DB_SQL_USER -p\$DB_SQL_PASS -h127.0.0.1 -P3306 Benchmarks -e\"' >> /home/ubuntu/.bashrc",
      "echo 'cd /home/ubuntu/faas-benchmarker && git pull' >> /home/ubuntu/.bashrc",

      # add crontab to run backup
      "echo \"1 1,13 * * * DB_SQL_USER=${var.DB_SQL_USER} DB_SQL_PASS=${var.DB_SQL_PASS} SPACE_NAME=${var.space_name} SPACE_KEY=${var.space_key} SPACE_SECRET_KEY=${var.space_secret_key} bash /home/ubuntu/faas-benchmarker/infrastructure/db_server_backups/backup.sh\" >> /home/ubuntu/cronfile",
      "crontab -u ubuntu /home/ubuntu/cronfile",

      # clone repository
      "git clone --quiet https://github.com/zanderhavgaard/faas-benchmarker /home/ubuntu/faas-benchmarker",

      # make directory for log files
      "mkdir -pv /home/ubuntu/logs/experiments",
      "mkdir -pv /home/ubuntu/logs/orchestration",
      "mkdir -pv /home/ubuntu/logs/error_logs",

      # copy the database docker compose file
      "cp /home/ubuntu/faas-benchmarker/infrastructure/db_server/docker-compose.yml /home/ubuntu/docker-compose.yml",

      # make sure ubuntu owns all of it's stuff...
      "chown -R \"ubuntu:ubuntu\" /home/ubuntu",

      "echo ======================================",
      "echo = Done setting up orchstrator server =",
      "echo ======================================",
    ]
  }
}

# wait for server to reboot and then start db with docker-compose
resource "null_resource" "user-provisioner" {
  depends_on = [null_resource.root-provisioner]

  provisioner "local-exec" {
    command = "until ssh ${var.username}@${digitalocean_droplet.db-server.ipv4_address} -i ${var.db_pvt_key} -o StrictHostKeyChecking=no -o ConnectTimeout=5 \"docker-compose up -d\" ; do sleep 5 ; done"
  }
}
