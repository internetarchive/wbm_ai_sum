# Use the official Python image as a base
FROM python:3.10-slim

# Set the working directory
WORKDIR /wbm_ai_sum

# Copy the requirements.txt file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire app to the container
COPY . .

# Expose the port that Streamlit will run on
EXPOSE 8501

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501

# Set the command to run your Streamlit app
CMD ["streamlit", "run", "main.py"]
