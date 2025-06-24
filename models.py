# -*- coding: utf-8 -*-
# models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

# Enum for transaction types (income, expense, asset_adjustment)
class TransactionType(enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"
    ASSET_ADJUSTMENT = "asset_adjustment"

# User model represents a WhatsApp user
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    whatsapp_number = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    transactions = relationship('Transaction', back_populates='user', cascade='all, delete-orphan')
    categories = relationship('Category', back_populates='user', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<User(whatsapp_number='{self.whatsapp_number}')>"

# Category model for income and expense categories
class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    type = Column(Enum(TransactionType), nullable=False) # e.g., 'income', 'expense'
    created_at = Column(DateTime, default=func.now())

    # Relationships
    user = relationship('User', back_populates='categories')
    transactions = relationship('Transaction', back_populates='category')

    def __repr__(self):
        return f"<Category(name='{self.name}', type='{self.type.value}')>"

# Transaction model for recording income, expenses, and asset adjustments
class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    type = Column(Enum(TransactionType), nullable=False) # 'income', 'expense', 'asset_adjustment'
    amount = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True) # Optional for asset adjustments
    notes = Column(String, nullable=True)
    transaction_date = Column(DateTime, default=func.now()) # Use func.now() for default
    created_at = Column(DateTime, default=func.now())

    # Relationships
    user = relationship('User', back_populates='transactions')
    category = relationship('Category', back_populates='transactions')

    def __repr__(self):
        return (f"<Transaction(type='{self.type.value}', amount={self.amount}, "
                f"category='{self.category.name if self.category else 'N/A'}', "
                f"date='{self.transaction_date.strftime('%Y-%m-%d')}')>")
