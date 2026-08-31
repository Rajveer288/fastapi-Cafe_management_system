from fastapi import APIRouter,HTTPException,status,Depends
from ..db import engine,Base,get_db
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..schemas import MenuCreate, MenuUpdate, UserInDB
from ..models import Menu
from ..auth import get_current_active_user,get_current_admin

router=APIRouter(
    prefix="/menu",
    tags=["menu"]
)

@router.post("/create",status_code=status.HTTP_201_CREATED)
def create(request: MenuCreate,
           db:Session=Depends(get_db),
           current_user:UserInDB=Depends(get_current_admin)):
    data=Menu(name=request.name,category=request.category,size=request.size,price=request.price,
              description=request.description,available=request.available)

    db.add(data)
    db.commit()
    db.refresh(data)
    return data
@router.get("/",status_code=status.HTTP_200_OK)
def get_menu(db:Session=Depends(get_db),
             current_user:UserInDB=Depends(get_current_active_user)):
    result=db.execute(select(Menu))
    menu=result.scalars().all()
    return menu
@router.get("/{id}",status_code=status.HTTP_200_OK)
def get_menu(id:int,db:Session=Depends(get_db),current_user:UserInDB=Depends(get_current_active_user)):
    result=db.execute(select(Menu).where(Menu.id==id))
    item=result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
    return item
@router.put("/{id}",status_code=status.HTTP_200_OK)
def update_menu(id:int,
                menu_update:MenuUpdate,
                db:Session=Depends(get_db),
                current_user:UserInDB=Depends(get_current_admin)):
    result=db.execute(select(Menu).where(Menu.id==id))
    item=result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
    update_data = menu_update.model_dump(exclude_unset=True)

    for key,value in update_data.items():
        setattr(item,key,value)

    db.commit()
    db.refresh(item)

    return item

@router.delete("/{id}",status_code=status.HTTP_200_OK)
def delete_menu(id:int,
                db:Session=Depends(get_db),
                current_user:UserInDB=Depends(get_current_admin)):
    result=db.execute(select(Menu).where(Menu.id==id))
    item=result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
    db.delete(item)
    db.commit()
    return {"Message":"Menu item deleted"}

@router.get("/category/{category}",status_code=status.HTTP_200_OK)
def get_menu_category(category:str,
                      db:Session=Depends(get_db),
                      current_user:UserInDB=Depends(get_current_active_user)):
    data=db.execute(select(Menu).where(Menu.category==category))
    result=data.scalars().all()
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return result





