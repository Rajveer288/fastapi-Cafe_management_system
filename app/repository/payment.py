from fastapi import APIRouter,HTTPException,status,Depends
from ..models import Order,Payment
from ..schemas import payment, UserInDB, PaymentUpdate,PaymentStatus
from ..db import get_db
from ..auth import get_current_active_user,get_current_admin
from sqlalchemy.orm import Session
from sqlalchemy import select

router = APIRouter(
    prefix="/payment",
    tags=["payment"]
)

@router.post('/create/{order_id}')
def create_payment(order_id:int,
                   request:payment,
                   db:Session=Depends(get_db),
                   current_user:UserInDB = Depends(get_current_active_user)):
    order=db.execute(
        select(Order).where(
            Order.order_id == order_id,
            Order.customer_id==current_user.id)
    ).scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Order not found")

    existing_payment=db.execute(
        select(Payment).where(
            Payment.order_id==order.order_id)
    ).scalar_one_or_none()
    if existing_payment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Payment already exists for this order")

    data=Payment(
        order_id=order.order_id,
        amount=order.total,
        payment_method=request.payment_method)
    db.add(data)
    db.commit()
    return data

@router.get('/get_all')
def get_all_payments(db:Session=Depends(get_db),
                     current_user:UserInDB=Depends(get_current_admin)):
    data=db.execute(select(Payment).order_by(Payment.id)).scalars().all()
    return data

@router.get('/status/pending')
def pending_status(db:Session=Depends(get_db),
                   current_user:UserInDB=Depends(get_current_admin)):
    data=db.execute(select(Payment).where(Payment.status==PaymentStatus.pending)).scalars().all()
    if not data:
        raise HTTPException(status_code=404,detail="No pending payments")
    return data

@router.get('/my/{order_id}')
def get_payment_user(order_id:int,
                db:Session=Depends(get_db),
                current_user:UserInDB=Depends(get_current_active_user)):
    data=db.execute(select(Payment).join(Order,Payment.order_id==Order.order_id).where(Payment.order_id==order_id,Order.customer_id==current_user.id)).scalar_one_or_none()
    if not data:
        raise HTTPException(status_code=404,detail="Invalid order_id")
    return data


@router.patch('/update/status/{order_id}')
def update_payment_status(order_id:int,
                          request:PaymentUpdate,
                          db:Session=Depends(get_db),
                          current_user:UserInDB=Depends(get_current_admin)):
    data=db.execute(select(Payment).where(Payment.order_id==order_id)).scalar_one_or_none()
    if not data:
        raise HTTPException(status_code=404,detail="Invalid order_id")
    data.status=request.status
    db.commit()
    db.refresh(data)
    return {"Message":"Payment status update successfully"}

@router.get('/{order_id}')
def get_payment_admin(order_id:int,db:Session=Depends(get_db),
                current_user:UserInDB=Depends(get_current_admin)):
    data=db.execute(select(Payment).where(Payment.order_id==order_id)).scalar_one_or_none()
    if not data:
        raise HTTPException(status_code=404,detail="Invalid order_id")
    return data



