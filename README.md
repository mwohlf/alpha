# Alpha Project

This project is a simple React frontend and FastAPI backend application using nx for build and deployment.

requirements for local host:
- node
- npm
- python3
- docker

## setup

this uses the config in alpha/package.json to install dependencies from the top level `package.json`
plus anything configured in the workspaces `frontend` and `backend`

```bash

# clean
cd alpha
rm -rf node_modules \
  package-lock.json \
  dist \
  frontend/node_modules \
  frontend/src/generated

# prepare
npm install

./nx reset
./nx init --no-interactive --nxCloud=false
./nx report


./nx build backend
./nx build frontend

# run
./nx serve backend
./nx serve frontend

```

The frontend will be running on `http://localhost:3000`. The frontend will automatically proxy requests to the backend.

The backend will be running on `http://127.0.0.1:8000`.


##

http://127.0.0.1:3000/index.html   - serving with backend by proxy

http://127.0.0.1:8000/index.html   - serving frontend by the backend


## Links

(ollama openAPI definition)[https://github.com/ollama/ollama/tree/main/docs]


todo:

pipx run openapi-python-client generate --path openapi.yaml

# This extracts the schema to a file named openapi.json
fastapi openapi main.py --output openapi.json
