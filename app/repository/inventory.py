from fastapi import APIRouter,status,HTTPException,Depends
from ..schemas import OrderCreate, OrderItemCreate, UserInDB, UpdateStatus,OrderStatus
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select,func
from ..db import get_db
from ..models import Order, Orderitem, Menu, User, Inventory
from ..auth import get_current_admin,get_current_active_user

router = APIRouter(
    prefix="/Inventory",
    tags=["Inventory"]
)

@router.post("/create")
def create_inventory(name:str,
                     quantity:float,
                     unit:str,
                     minimum_stock:float,
                     db:Session=Depends(get_db),
                     current_user:UserInDB=Depends(get_current_active_user)):
    data=Inventory(name=name,
                   quantity=quantity,
                   unit=unit,
                   minimum_stock=minimum_stock,)
    db.add(data)
    db.commit()
    db.refresh(data)

    return data

@router.get("/all")
def get_all_inventory(db:Session=Depends(get_db),current_user:UserInDB=Depends(get_current_admin)):
    inventory=db.execute(
        select(Inventory)
    ).scalars().all()
    if not inventory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Inventory not found")

    return inventory

@router.get("/{inventory_id}")
def get_inventory_by_id(inventory_id:int,db:Session=Depends(get_db),
                        current_user:UserInDB=Depends(get_current_admin)):
    inventory=db.execute(
        select(Inventory).where(Inventory.id == inventory_id)
    ).scalar_one_or_none()
    if inventory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Inventory not found")
    return inventory
@router.put("/update/{inventory_id}")
def update_inventory(inventory_id:int,name:str,quantity:float,
                     unit:str,minimum_stock:float,db:Session=Depends(get_db),
                     current_user:UserInDB=Depends(get_current_admin)):
    inventory=db.execute(
        select(Inventory).where(
            Inventory.id==inventory_id
        )
    ).scalar_one_or_none()

    if inventory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,detail="Inventory not found"
        )
    inventory.name=name
    inventory.quantity=quantity
    inventory.unit=unit
    inventory.minimum_stock=minimum_stock

    if inventory.quantity<=0:
        inventory.available=False
    else:
        inventory.available=True

    db.commit()
    db.refresh(inventory)
    return inventory

@router.delete("/delete/{inventory_id}")
def delete_inventory(inventory_id:int,
                     db:Session=Depends(get_db),
                     current_user:UserInDB=Depends(get_current_admin)):
    inventory=db.execute(
        select(Inventory).where(
            Inventory.id==inventory_id
        )
    ).scalar_one_or_none()

    if inventory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory not found"
        )
    db.delete(inventory)
    db.commit()

    return {
        "message":"Inventory deleted successfully"
    }
@router.post("/order/{inventory_id}")
def order_inventory(inventory_id:int,
                    db:Session=Depends(get_db),
                    current_user:UserInDB=Depends(get_current_admin)):
    inventory=db.execute(
        select(Inventory).where(Inventory.id == inventory_id)
    ).scalar_one_or_none()
    if inventory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Inventory not found")

    if inventory.quantity>=inventory.maximum_stock:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inventory is already at maximum stock")

    order_quantity=inventory.maximum_stock-inventory.quantity

    inventory.quantity+=order_quantity

    db.commit()
    db.refresh(inventory)

    return {
        "message":f"{inventory.name} ordered successfully",
        "ordered_quantity":order_quantity,}


