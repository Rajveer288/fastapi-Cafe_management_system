from fastapi import FastAPI,HTTPException,status
from . import models
from app.repository import menu,inventory,order,customer,payment
from . import auth

from .db import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(menu.router)
app.include_router(inventory.router)
app.include_router(order.router)
app.include_router(auth.router)
app.include_router(customer.router)
app.include_router(payment.router)

