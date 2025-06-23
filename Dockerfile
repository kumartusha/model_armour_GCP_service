# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy your app files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose default Streamlit port
EXPOSE 8080

# Streamlit runs on 8501 by default, so override to use 8080 for Cloud Run
ENV PORT=8080

# Set Streamlit to run on 0.0.0.0 and use Cloud Run port
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
