# AI Bootcamp Notebooks - Jupyter Lab Dockerfile
FROM jupyter/scipy-notebook:python-3.11

# Set working directory
WORKDIR /home/jovyan/work

# Install system dependencies
USER root
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Switch back to jovyan user
USER jovyan

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional Jupyter extensions
RUN pip install --no-cache-dir \
    jupyterlab-git \
    jupyterlab-lsp \
    python-lsp-server[all] \
    jupyterlab-widgets \
    ipywidgets

# Copy notebook files
COPY . .

# Set environment variables
ENV JUPYTER_ENABLE_LAB=yes
ENV JUPYTER_TOKEN=ai-bootcamp-2024
ENV PYTHONPATH=/home/jovyan/work

# Expose port
EXPOSE 8888

# Start Jupyter Lab
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--NotebookApp.token='ai-bootcamp-2024'"]
