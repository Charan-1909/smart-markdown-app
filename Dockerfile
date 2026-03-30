# 1. Use an official, lightweight Python image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of your application code
COPY . .

# 5. Expose the port Streamlit uses
EXPOSE 8501

# 6. Add a healthcheck to ensure the container is running properly
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# 7. Command to run the Streamlit app
# Setting the address to 0.0.0.0 is required for Docker!
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]