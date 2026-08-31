from fastapi import APIRouter,status,HTTPException,Depends
from ..schemas import OrderCreate, OrderItemCreate, UserInDB, UpdateStatus,OrderStatus
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select,func
from ..db import get_db
from ..models import Order, Orderitem, Menu, User, Recipe, Inventory
from ..auth import get_current_admin,get_current_active_user

router = APIRouter(
    prefix="/order",
    tags=["order"]
)

@router.post("/create")
def create_order(request: OrderCreate,
                 db: Session = Depends(get_db),
                 current_user:UserInDB=Depends(get_current_active_user)):
    order_items=[]
    total=0

    inventory_changes=[]

    for item in request.items:
        menu=db.execute(
            select(Menu).where(
                Menu.id==item.menu_id)
        ).scalar_one_or_none()

        if menu is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Menu item {item.menu_id} not found")

        if not menu.available:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"{menu.name} is not available")

        recipes=db.execute(
            select(Recipe).where(
                Recipe.menu_id==item.menu_id
            )
        ).scalars().all()

        if not recipes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No recipe found for {menu.name}")

        for recipe in recipes:

            inventory=db.execute(
                select(Inventory).where(
                    Inventory.id==recipe.inventory_id
                )
            ).scalar_one_or_none()

            if inventory is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Inventory item not found"
                )
            required_quantity=recipe.quantity_required*item.quantity

            if inventory.quantity < required_quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Not enough {inventory.name}. "
                        f"Required: {required_quantity} {inventory.unit}, "
                        f"Available: {inventory.quantity} {inventory.unit}"
                    )
                )

            inventory_changes.append(
                (inventory,required_quantity)
            )


        item_total=menu.price*item.quantity
        total+=item_total

        order_items.append(
            Orderitem(
                menu_id=item.menu_id,
                quantity=item.quantity,
                price=item_total
            )
        )
    order=Order(

        customer_id=current_user.id,
        total=total,
    )
    db.add(order)
    db.flush()

    for item in order_items:
        item.order_id=order.order_id
        db.add(item)

    for inventory,required_quantity in inventory_changes:
        inventory.quantity-=required_quantity

        if inventory.quantity <=0:
            inventory.available=False


    db.commit()

    return order

@router.get("/all")
def get_all_orders(db: Session = Depends(get_db),
                   current_user:UserInDB=Depends(get_current_admin)):
    orders=db.execute(
        select(Order.order_id,
               Order.customer_id,
               Order.status,
               Order.total
               )).mappings().all()
    if not orders:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='orders not found')
    return orders

@router.get("/{order_id}")
def get_order_by_id(order_id:int,
                    db: Session = Depends(get_db),
                    current_user:UserInDB=Depends(get_current_admin)):
    data = db.execute(
        select(
            Order.order_id,
            Order.customer_id,
            User.username,
            Order.status,
            Order.total
        ).join(User,Order.customer_id==User.id).where(
            Order.order_id == order_id)
    ).mappings().first()
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    orders=db.execute(
        select(
            Orderitem.menu_id,
            Orderitem.quantity,
            Orderitem.price
        ).where(Orderitem.order_id == data["order_id"])
    ).mappings().all()

    return{
        "order_id":data["order_id"],
        "customer_id":data["customer_id"],
        "username":data["username"],
        "status":data["status"],
        "total":data["total"],
        "items":[{
            "menu_id":order["menu_id"],
            "quantity":order["quantity"],
            "price":order["price"]
        }for order in orders]
    }


@router.put("/update/{order_item_id}")
def update_order(order_item_id:int,
                 request:OrderItemCreate,
                 current_user:UserInDB=Depends(get_current_admin),
                 db:Session = Depends(get_db),):
    data=db.execute(
        select(Orderitem).where(
            Orderitem.id == order_item_id)
    ).scalar_one_or_none()
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Order item not found")


    menu=(db.execute(
        select(Menu).where(
            Menu.id==request.menu_id)
    ).scalar_one_or_none())

    if menu is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Menu Item not found')

    if not menu.available:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{menu.name} is not available")

    new_recipes = db.execute(
        select(Recipe).where(
            Recipe.menu_id == request.menu_id
        )
    ).scalars().all()

    if not new_recipes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No recipe found for {menu.name}"
        )

    # Old recipe
    old_recipes = db.execute(
        select(Recipe).where(
            Recipe.menu_id == data.menu_id
        )
    ).scalars().all()

    inventory_changes = {}

    for recipe in old_recipes:
        old_quantity = (
                recipe.quantity_required * data.quantity
        )

        inventory_changes[recipe.inventory_id] = (
                inventory_changes.get(recipe.inventory_id, 0)
                + old_quantity
        )

    for recipe in new_recipes:
        new_quantity = (
                recipe.quantity_required * request.quantity
        )

        inventory_changes[recipe.inventory_id] = (
                inventory_changes.get(recipe.inventory_id, 0)
                - new_quantity
        )

    for inventory_id, change in inventory_changes.items():

        inventory = db.execute(
            select(Inventory).where(
                Inventory.id == inventory_id
            )
        ).scalar_one_or_none()

        if inventory is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory not found"
            )

        if change < 0:
            required = abs(change)
            if inventory.quantity < required:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Not enough {inventory.name}. "
                        f"Required: {required} {inventory.unit}, "
                        f"Available: {inventory.quantity} {inventory.unit}"
                    )
                )

    for inventory_id, change in inventory_changes.items():
        inventory = db.execute(
            select(Inventory).where(
                Inventory.id == inventory_id
            )
        ).scalar_one()
        inventory.quantity += change

        if inventory.quantity <= 0:
            inventory.available = False
        else:
            inventory.available = True


    new_price = menu.price * request.quantity

    data.menu_id=request.menu_id
    data.quantity=request.quantity
    data.price=new_price

    items=db.execute(
        select(Orderitem).where(
            Orderitem.order_id==data.order_id)
    ).scalars().all()

    total=sum(item.price for item in items)

    order=db.execute(
        select(Order).where(
            Order.order_id==data.order_id)
    ).scalar_one()

    order.total=total

    db.commit()
    db.refresh(data)
    return {'message':'updated successfully',
            "order_id": data.order_id,
            "order_item_id": data.id,
            "menu_id": data.menu_id,
            "quantity": data.quantity,
            "price": data.price,
            "total": order.total
            }

@router.delete("/delete/{id}")
def order_delete(id:int,
                 db:Session = Depends(get_db),
                 current_user:UserInDB=Depends(get_current_admin)):
    data=db.execute(
        select(Order).where(
            Order.order_id == id,Order.status==OrderStatus.cancelled)
    ).scalar_one_or_none()
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Order not found")
    items=db.execute(
        select(Orderitem).where(Orderitem.order_id==id)
    ).scalars().all()
    for item in items:
        db.delete(item)

    db.delete(data)
    db.commit()
    return {'message':'Order deleted successfully'}

@router.patch('/update/status/{order_id}')
def update_status(order_id:int,
                  updated_status:UpdateStatus,
                  db:Session = Depends(get_db),
                  current_user:UserInDB=Depends(get_current_admin)):
    data=db.execute(
        select(Order).where(
            Order.order_id == order_id)
    ).scalar_one_or_none()
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Order item not found")
    data.status=updated_status.status
    db.commit()
    db.refresh(data)
    return {'message':'updated status successfully'}

@router.patch("/cancel/{order_id}")
def cancel_order(order_id:int,db:Session=Depends(get_db),current_user:UserInDB=Depends(get_current_admin)):
    data=db.execute(
        select(Order).where(
            Order.order_id == order_id
        )
    ).scalar_one_or_none()
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail="Order not found")
    if data.status in [OrderStatus.done,OrderStatus.cancelled]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Order cannot be canceled")

    items=db.execute(
        select(Orderitem).where(
            Orderitem.order_id == order_id
        )
    ).scalars().all()
    for item in items:
        recipes = db.execute(
            select(Recipe).where(
                Recipe.menu_id == item.menu_id
            )
        ).scalars().all()

        for recipe in recipes:
            inventory = db.execute(
                select(Inventory).where(
                    Inventory.id == recipe.inventory_id
                )
            ).scalar_one_or_none()
            if inventory is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail="Inventory not found")
            required_quantity =(recipe.quantity_required*item.quantity)
            inventory.quantity+=required_quantity
            inventory.available=True

    data.status=OrderStatus.cancelled


    db.commit()
    db.refresh(data)

    return{
        "message":"Order cancelled successfully",
        "order_id":data.order_id,
        "customer_id":data.customer_id,
    }







