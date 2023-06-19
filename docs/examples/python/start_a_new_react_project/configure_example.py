from fastapi import FastAPI

from reactpy.backend.fastapi import configure

asgi_app = FastAPI()
configure(asgi_app)
