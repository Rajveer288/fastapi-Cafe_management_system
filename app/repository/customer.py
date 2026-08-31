from fastapi import APIRouter,HTTPException,Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..schemas import UserInDB,UpdateUser
from . import order
from ..db import get_db
from ..models import User,Order
from ..auth import get_current_admin

router = APIRouter(
    prefix="/customer",
    tags=["customer"]
)

@router.get("/")
def get_customer_details(current_user: UserInDB = Depends(get_current_admin),db:Session = Depends(get_db)):
    users=(db.execute(select(User.id,User.username,User.email,User.is_active,User.role,)).all())
    if not users:
        raise HTTPException(status_code=404,
                            detail="No customer found")
    result=[]
    for user in users:
        orders=db.execute(
            select(Order).where(Order.customer_id == user.id)
        ).scalars().all()

        result.append({
            "id":user.id,
            "name":user.username,
            "email":user.email,
            "is_active":user.is_active,
            "role":user.role,
            "orders":[
                {
                "order_id":order.order_id,
                "status":order.status,
                "total":order.total
                } for order in orders
            ]
        })
    return result

@router.get("/{id}")
def get_customer_by_id(id:int,db:Session = Depends(get_db),current_user: UserInDB = Depends(get_current_admin)):
    user=db.execute(select(User.id,User.username,User.email,User.is_active,User.role,).where(User.id==id)).first()
    if user is None:
        raise HTTPException(status_code=404,detail="No customer found")

    orders=db.execute(
        select(Order).where(Order.customer_id == user.id)
    ).scalars().all()
    return{
        "id":user.id,
        "name":user.username,
        "email":user.email,
        "is_active":user.is_active,
        "role":user.role,
        "orders":[{
            "order_id":order.order_id,
            "status":order.status,
            "total":order.total}
        for order in orders]
    }

@router.delete("/{id}")
def delete_customer(id:int,db:Session=Depends(get_db),current_user: UserInDB = Depends(get_current_admin)):
    user=db.execute(select(User).where(User.id == id)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404,detail="No customer found")
    db.delete(user)
    db.commit()
    return {"message":"Deleted customer successfully"}

@router.put("/{id}")
def update_customer(request:UpdateUser,id:int,db:Session=Depends(get_db),current_user: UserInDB = Depends(get_current_admin)):
    user = db.execute(select(User).where(User.id == id)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="No customer found")

    user.username = request.username
    user.email = request.email
    user.is_active = request.is_active
    user.role = request.role
    db.commit()
    return {"message":"Updated customer successfully"}


