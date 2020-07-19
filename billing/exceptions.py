class BillingError(Exception):
    pass


class NotFound(BillingError):
    pass


class LackOfMoney(BillingError):
    pass
