FROM python:3.9.7

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt ./

# Install dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the entire project directory (including app.py) to the working directory
COPY . .

# Run the applicationç
CMD ["python3.9", "app/app.py"]
