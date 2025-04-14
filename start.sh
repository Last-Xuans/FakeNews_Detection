#!/bin/bash
chmod +x ./run.sh
docker build -t fake-news-detector .
docker run -p 7860:7860 fake-news-detector
