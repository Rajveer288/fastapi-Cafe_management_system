from .db import Sessionlocal,engine,Base
from fastapi import HTTPException,status
from .menu_data import menu_items
from .inventory_data import inventory_items
from .recipe_data import recipe_items
from sqlalchemy import select
from . import models
from .auth import get_password_hash

Base.metadata.create_all(bind=engine)

def seed_data():
    db= Sessionlocal()

    try:
        #setting the admin here
        existing_admin = db.execute(select(models.User).where(models.User.role == 'admin')).first()
        if existing_admin:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='user already exists')
        new_admin = models.User(
            username="rajveer",
            email="rajveersinghtanwar28@gmail.com",
            hashed_password=get_password_hash("rajveertanwar_28"),
            is_active=True,
            role='admin',
        )
        db.add(new_admin)
        db.commit()
        print('admin created successfully')

        #storing all the values

        db.add_all(menu_items)
        db.add_all(inventory_items)
        db.add_all(recipe_items)
        db.commit()
        print("Menu,recipe and inventory added successfully")
    except Exception as error:
        db.rollback()
        print('error',error)
    finally:
        db.close()

seed_data()

