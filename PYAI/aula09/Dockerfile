FROM continuumio/miniconda3 
WORKDIR /app
COPY environment.yml .
RUN conda env create -f environment.yml
COPY . .
WORKDIR /app/-genaiufpr-fastapi
CMD ["conda", "run", "--no-capture-output", "-n", "clima_api", "uvicorn", "--host", "0.0.0.0", "--port", "8000", "clima_api:app"]
