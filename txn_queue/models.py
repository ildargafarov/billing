import attr
from decimal import Decimal
from datetime import datetime
import json
import uuid


@attr.s(slots=True, frozen=True)
class Transaction:
    amount: Decimal = attr.ib()
    credit_account_id: str = attr.ib()
    debit_account_id: str = attr.ib()
    create_date: datetime = attr.ib(factory=datetime.now)
    key: str = attr.ib(factory=uuid.uuid4)

    @classmethod
    def from_data(cls,
                  amount: float,
                  credit_account_id: str,
                  debit_account_id: str):
        return cls(
            Decimal.from_float(amount),
            credit_account_id,
            debit_account_id)

    @classmethod
    def from_dump(cls, dump: str):
        data = json.loads(dump)
        return cls(
            Decimal.from_float(data["amount"]),
            data["credit_account_id"],
            data["debit_account_id"],
            datetime.fromtimestamp(data["create_date"])
        )

    def dump(self) -> str:
        return json.dumps({
            float(self.amount),
            self.credit_account_id,
            self.debit_account_id,
            self.create_date.timestamp()
        })
