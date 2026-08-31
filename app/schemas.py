from pydantic import BaseModel, ConfigDict
from enum import Enum
from typing import List

class Token(BaseModel):
    access_token:str
    token_type:str

class TokenData(BaseModel):
    username:str=None

class User(BaseModel):
    id:int
    username:str
    email:str
    is_active:bool=True
    role: str

    model_config=ConfigDict(from_attributes=True)

class UserInDB(User):
    hashed_password:str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class MenuCreate(BaseModel):
    name: str
    category: str
    size: str
    price: float
    description: str|None=None
    available: bool=True

class MenuUpdate(BaseModel):
    name: str
    size: str
    price: float
    description: str | None = None
    available: bool = True

class InventoryCreate(BaseModel):
    name: str
    quantity: float
    unit: str
    minimum_stock:float
    available:bool=True

class InventoryUpdate(BaseModel):
    name: str
    quantity: float
    unit: str
    minimum_stock:float
    available:bool=True

class InventoryPatch(BaseModel):
    quantity: float
    class Config:
        from_attribute = True

class OrderItemCreate(BaseModel):
    menu_id: int
    quantity: int

class OrderStatus(str,Enum):
    pending = "pending"
    preparing = "preparing"
    served = "served"
    done = "done"
    cancelled = "cancelled"

class UpdateStatus(BaseModel):
    status: OrderStatus



class OrderCreate(BaseModel):
    items: List[OrderItemCreate]

class UpdateUser(BaseModel):
    username:str
    email:str
    is_active:bool=True
    role: str

class PaymentMethod(str, Enum):
    UPI = "upi"
    CARD = "card"
    CASH = "cash"
    NET_BANKING = "net_banking"
    WALLET = "wallet"

class payment(BaseModel):
    payment_method:PaymentMethod

class PaymentStatus(str, Enum):
    pending = "pending"
    success = "success"
    failure = "failure"
    cancelled = "cancelled"

class PaymentUpdate(BaseModel):
    status: PaymentStatus


