FROM python:3.10-slim

# सभी जरूरी पैकेज एक साथ इंस्टॉल
RUN apt-get update && apt-get install -y \
    ffmpeg \
    nodejs \
    npm \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy application
COPY . /app/
WORKDIR /app/

# पायथन पैकेज इंस्टॉल करें
RUN pip install -r requirements.txt

# Start application
CMD bash start
