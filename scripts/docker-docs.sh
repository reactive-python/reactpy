docker build -t foo -f docs/Dockerfile .
docker run -it -p 5000:5000 --rm foo
