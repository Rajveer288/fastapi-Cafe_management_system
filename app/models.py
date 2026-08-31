from sqlalchemy import Column,Float,Integer,String,Boolean,ForeignKey,Enum as SQLEnum
from .db import Base
from .schemas import OrderStatus,PaymentStatus,PaymentMethod


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True,index=True)
    username = Column(String,unique=True,nullable=False)
    email = Column(String,unique=True,nullable=False)
    hashed_password = Column(String,nullable=False)
    is_active = Column(Boolean,default=True)
    role=Column(String,nullable=False,default='customer')

class Menu(Base):
    __tablename__ = "menu"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    size = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    available = Column(Boolean, default=True)

class Inventory(Base):
    __tablename__ = "inventory"

    id=Column(Integer, primary_key=True, index=True)
    name=Column(String, nullable=False)
    quantity=Column(Float, nullable=False)
    unit=Column(String, nullable=False)
    minimum_stock=Column(Float, nullable=False)
    maximum_stock=Column(Float, nullable=False)
    available=Column(Boolean, nullable=False,default=True)

class Order(Base):
    __tablename__ = "orders"
    order_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer,ForeignKey('users.id'), nullable=False)
    total = Column(Float, nullable=False)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.pending)

class Orderitem(Base):
    __tablename__ = "order_items"
    id=Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer,ForeignKey('orders.order_id'), nullable=False)
    menu_id = Column(Integer,ForeignKey('menu.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)

class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True)
    menu_id = Column(Integer,ForeignKey('menu.id'), nullable=False)
    inventory_id = Column(Integer,ForeignKey('inventory.id'), nullable=False)
    quantity_required= Column(Float, nullable=False)

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    order_id=Column(Integer,ForeignKey('orders.order_id'))
    amount=Column(Float,nullable=False)
    payment_method=Column(SQLEnum(PaymentMethod),nullable=False,)
    status=Column(SQLEnum(PaymentStatus),default=PaymentStatus.pending)