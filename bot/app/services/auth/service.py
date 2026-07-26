from app.services.employees.service import (
    get_employee
)


async def check_access(
    telegram_id:int
):


    employee = await get_employee(
        telegram_id
    )


    if employee is None:

        return False


    if not employee.active:

        return False


    return employee
