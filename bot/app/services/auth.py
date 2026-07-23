from app.services.employee_service import get_employee


async def get_user_role(telegram_id: int):

    employee = await get_employee(
        telegram_id
    )

    if not employee:
        return None


    return employee["role"]
