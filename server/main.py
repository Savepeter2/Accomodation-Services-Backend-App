from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path('.')/'.env')

from fastapi import FastAPI, Depends, HTTPException, status, Request


from app.database import engine,Base
from routers.user import router as user_router

import uvicorn
import argparse


#take in port as argument
# try:
#     parser = argparse.ArgumentParser()
#     parser.add_argument('--port', type=int, default=8000)
#     args = parser.parse_args()
#     port = args.port
# except:
#     print("here")
#     pass

Base.metadata.create_all(bind=engine)
app = FastAPI()

app.include_router(user_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)