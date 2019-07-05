# This script exists because of my ignorance of docker/docker-compose
# Attempting to build the darkchess-client image fails because it
# doesn't have certain file permissions in the 'data/' folder,
# however that folder can't be ignored by docker-compose so the
# following .dockerignore can't stick around.
echo "data/" > .dockerignore
docker build -t darkchess-client:latest .
rm .dockerignore
