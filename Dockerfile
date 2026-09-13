FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    make \
    && rm -rf /var/lib/apt/lists/*

RUN pip install numpy==2.5.1 pandas==3.0.5 yfinance==1.5.2 scipy==1.18.0

COPY . .

CMD ["make", "all"]
