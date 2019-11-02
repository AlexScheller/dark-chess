# API

## Deployment/Devops

*Some of the content below consists of notes for development, and isn't
necessary to follow along with for your own deployment.*

Here's a command to run a local docker container for MySQL. Replace the
variables as necessary

`docker run --name mysql -d -h 127.0.0.1 -p 3306:3306 -e MYSQL_RANDOM_ROOT_PASSWORD=yes -e MYSQL_DATABASE=<dbname> -e MYSQL_USER=<dbuser> -e MYSQL_PASSWORD=<dbpass> mysql/mysql-server:5.7`