# API

## State of the database

### Migrations

Until we actually release some sort of initial beta version, the initial
migration will continually change.

## Deployment/Devops

*Some of the content below consists of notes for development, and isn't
necessary to follow along with for your own deployment.*

Here's a command to run a local docker container for MySQL. Replace the
variables as necessary

`docker run --name mysql -d -h 127.0.0.1 -p 3306:3306 -e MYSQL_RANDOM_ROOT_PASSWORD=yes -e MYSQL_DATABASE=<dbname> -e MYSQL_USER=<dbuser> -e MYSQL_PASSWORD=<dbpass> mysql/mysql-server:5.7`

Here's a similar one for Postgres

`docker run --rm --name postgres -d -p 5432:5432 -e POSTGRES_PASSWORD=<dbpass> -e POSTGRES_USER=<dbuser> -e POSTGRES_DB=<database> postgres`

Which can then be connected to with:

`docker exec -it postgres psql -U postgres`