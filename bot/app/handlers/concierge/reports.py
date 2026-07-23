from aiogram import Router, F
from aiogram.types import Message


from app.services.report import get_concierge_report



router = Router()



@router.message(
    F.text == "📊 Отчеты"
)
async def concierge_reports(
    message: Message
):


    report = await get_concierge_report()



    await message.answer(

        f"""
📊 Отчеты Renome OPS


📋 Заявки и задачи:

Всего:
{report['tasks_total']}

✅ Выполнено:
{report['tasks_done']}

⏳ В работе:
{report['tasks_work']}



📦 Доставки:

{report['deliveries']}



🔑 Ключи:

{report['keys']}



📄 Документы:

{report['documents']}

"""

    )
