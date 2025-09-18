# 1. Start with a modern, stable, and small base image.
FROM python:3.13-slim

# 2. Set the working directory inside the container. This is our "package root".
WORKDIR /app

# 3. Add the project root to the PYTHONPATH.
#    This is the key fix. It tells Python to look for modules in the /app
#    directory, allowing clean, absolute imports to work everywhere.
ENV PYTHONPATH=/app

# 4. Copy only the dependencies list first to leverage Docker's cache.
COPY requirements.txt .

# 5. Install the dependencies into the container's Python environment.
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of the application source code into the working directory.
COPY . .

# 7. Expose the port that the application will run on.
EXPOSE 8000

# 8. Define the default command to run when the container starts.
#    We can now go back to the simpler uvicorn command because PYTHONPATH
#    has solved the import issues.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

