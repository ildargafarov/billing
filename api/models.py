from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

default_json_encoders = {
    datetime: lambda v: v.isoformat()
}


class TransactionModel(BaseModel):
    amount: float
    credit_account_id: Optional[str] = Field(None,
                                             alias='creditAccountId')
    debit_account_id: str = Field(...,
                                  min_length=1,
                                  alias='debitAccountId')
    create_date: datetime = Field(datetime.now(),
                                  alias='createDate')

    class Config:
        json_encoders = {
            datetime: lambda v: v.timestamp()
        }


class CustomerModel(BaseModel):
    id: int
    register_date: datetime = Field(..., alias='registerDate')

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        json_encoders = default_json_encoders


class CustomersModel(BaseModel):
    __root__: List[CustomerModel]


class AccountModel(BaseModel):
    id: str
    balance: float
    customer_id: int = Field(..., alias='customerId')
    create_date: datetime = Field(..., alias='createDate')

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        json_encoders = default_json_encoders


class AccountsModel(BaseModel):
    __root__: List[AccountModel]


class RegisterCustomerModel(BaseModel):
    customer_id: int = Field(..., alias='customerId')
    account_id: str = Field(..., alias='accountId')

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class OperationModel(BaseModel):
    amount: float
    balance: float
    date: datetime

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        json_encoders = default_json_encoders


class AccountOperationsModel(BaseModel):
    account_id: str = Field(..., alias='accountId')
    balance: float
    create_date: datetime = Field(..., alias='createDate')
    customer_id: int = Field(..., alias='customerId')
    operations: List[OperationModel]

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        json_encoders = default_json_encoders
