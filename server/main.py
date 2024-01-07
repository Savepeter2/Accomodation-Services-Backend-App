from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path('.')/'.env')

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.staticfiles import StaticFiles
from decouple import config
from app.database import engine,Base
from routers.user import router as user_router
from routers.acc_provider import router as acc_prov_router
from routers.service_provider import router as serv_prov_router
from routers.explorer import router as explorer_router
from routers.admin import router as admin_router
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import argparse
import os

RENDER_DIR = config("RENDER_DIR")
#take in port as argument
origins = ["*"]
methods = ["*"]
headers = ["*"]

try:
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    port = args.port
except:
    print("here")
    pass

BASEDIR = os.path.abspath(os.path.dirname(__file__))
BASEDIR = os.path.join(BASEDIR, "app")

Base.metadata.create_all(bind=engine)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=methods,
    allow_headers=headers,
)

app.include_router(user_router)
app.include_router(acc_prov_router)
app.include_router(explorer_router)
app.include_router(admin_router)

# app.mount("/static", StaticFiles(directory=BASEDIR+"\statics"), name="static")
app.mount("/static", StaticFiles(directory=RENDER_DIR), name="static")
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)