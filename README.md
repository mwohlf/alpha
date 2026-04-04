# Alpha Project

This project is a simple React frontend and FastAPI backend application using nx for build and deployment.

requirements for local host:
- node
- npm
- python3
- docker

<br>

## setup

this uses the config in alpha/package.json to install dependencies from the top level `package.json`
plus anything configured in the workspaces `frontend` and `backend`

```bash
cd alpha
```
<br>

clean:
```bash
rm -rf \
  .nx/cache \
  .nx/installation \
  .nx/workspace-data \
  node_modules \
  package-lock.json \
  dist \
  backend/.venv \
  backend/.ruff_cache \
  backend/__pycache__ \
  frontend/dist \
  frontend/node_modules \
  frontend/src/generated \
  etc/alpha-service.yaml \
  package-lock.json

npm install
```
<br>

prepare:
```bash
./nx reset
./nx init --no-interactive --nxCloud=false
./nx report
```
<br>

build:
```bash
./nx build backend
./nx build frontend
```
<br>

run:
```bash
./nx serve backend
./nx serve frontend
```  
<br>


create docker image and run local:
```bash
./nx build_docker backend
docker run -p 8000:8000 alpha-app
```
<br>

## details

The frontend will be running on `http://localhost:3000`. The frontend will automatically proxy requests to the backend.

The backend will be running on `http://127.0.0.1:8000`.

<br>

CI build:
```bash
cd alpha
npm install
./nx build_docker backend
```
This actually builds the backend twice, once for loca use, once in the multi-stage docker build.


running local:

http://127.0.0.1:3000/index.html   - serving with backend by proxy

http://127.0.0.1:8000/index.html   - serving frontend by the backend

<br>


## links

(ollama openAPI definition)[https://github.com/ollama/ollama/tree/main/docs]

