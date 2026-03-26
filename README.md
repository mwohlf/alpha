# Alpha Project

This project is a simple React frontend and FastAPI backend application.

## Running the application

### Backend

1. Navigate to the `backend` directory.
2. Activate the virtual environment: `source .venv/bin/activate`
3. Start the backend server: `uvicorn main:app --reload`

or just:  `npx nx serve backend` in root


The backend server will be running on `http://127.0.0.1:8000`.

### Frontend

1. Navigate to the `frontend` directory.
2. Install the dependencies: `npm install`
3. Install the dependencies: `npm run build`
4. Start the frontend development server: `npm run dev`

The frontend will be running on `http://localhost:3000`. The frontend will automatically proxy requests to the backend.



### Links

(ollama openAPI definition)[https://github.com/ollama/ollama/tree/main/docs]




### setup

requirements for local host:
- node
- npm


#### bootstrap with local npm

this uses the config in package.json to install `nx` and `rimraf` from the top level `package.json`
plus anything configured in the workspaces `frontend` and `backend`
```bash
cd alpha
rm -rf node_modules package-lock.json
npm install
```

#### fire up the project setup with nx
./nx reset
./nx init --no-interactive --nxCloud=false
./nx report

./nx orval frontend
./nx serve frontend




./nx clean alpha
./nx setup alpha
./nx run alpha


