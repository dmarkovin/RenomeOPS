from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandObject


from app.services.employee_service import (
    get_employee,
    get_employee_by_invite,
    activate_employee
)


from app.keyboards.main import admin_menu
from app.keyboards.concierge import concierge_keyboard
from app.keyboards.director import director_keyboard
from app.keyboards.executor import executor_keyboard


router = Router()



async def send_role_menu(
    message: Message,
    employee
):

    role = employee["role"]


    if role == "SUPER_ADMIN":

        await message.answer(
            """
👑 Renome OPS

Роль:
Супер Администратор
""",
            reply_markup=admin_menu()
        )


    elif role == "DIRECTOR":

        await message.answer(
            """
👨‍💼 Renome OPS

Роль:
Директор
""",
            reply_markup=director_keyboard()
        )


    elif role == "CONCIERGE":

        await message.answer(
            """
🛎 Renome OPS

Роль:
Консьерж Сервис
""",
            reply_markup=concierge_keyboard()
        )


    elif role in [
        "TECHNICIAN",
        "CLEANING",
        "SECURITY"
    ]:

        await message.answer(
            """
🔧 Renome OPS

Рабочее меню сотрудника
""",
            reply_markup=executor_keyboard()
        )


    else:

        await message.answer(
            """
⚠️ Роль не определена.
Обратитесь к администратору.
"""
        )





@router.message(
    Command("start")
)
async def start_handler(
    message: Message,
    command: CommandObject
):


    telegram_id = message.from_user.id

    username = message.from_user.username



    # Проверяем уже зарегистрированного сотрудника

    employee = await get_employee(
        telegram_id
    )


    if employee:

        await send_role_menu(
            message,
            employee
        )

        return




    # Проверяем приглашение


    if command.args:


        invite_code = command.args.strip()



        employee = await get_employee_by_invite(
            invite_code
        )



        if employee:


            activated = await activate_employee(
                employee["id"],
                telegram_id,
                username
            )



            await message.answer(
                f"""
✅ Доступ активирован!


Добро пожаловать в Renome OPS


👤 {activated['full_name']}


🏢 Подразделение:

{activated['team']}
"""
            )



            await send_role_menu(
                message,
                activated
            )


            return




    await message.answer(
        """
👋 Добро пожаловать в Renome OPS!


Ваш Telegram еще не зарегистрирован.


Если у вас есть приглашение,
перейдите по ссылке от администратора.
"""
    )
