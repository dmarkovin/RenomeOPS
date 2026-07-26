async def send_notification(
    bot,
    telegram_id,
    text
):

    if not telegram_id:
        return


    await bot.send_message(
        telegram_id,
        text
    )



async def notify_new_task(
    bot,
    task
):

    pass



async def notify_assigned(
    bot,
    task,
    employee
):

    pass



async def notify_status_changed(
    bot,
    task
):

    pass
