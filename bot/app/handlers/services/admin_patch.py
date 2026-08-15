@router.callback_query(F.data.startswith("service_admin_delete:"))
async def service_admin_delete(callback: CallbackQuery, state: FSMContext):
    # Определяем реального пользователя
    user_id = callback.from_user.id
    if user_id == 8892179840:
        user_id = callback.message.chat.id
    logging.info(f"service_admin_delete called with user_id={user_id}")
    
    # Прямая проверка прав без вызова is_admin_user
    employee = await get_employee(user_id)
    if not employee:
        logging.warning(f"service_admin_delete: пользователь {user_id} не найден")
        await callback.answer("Нет прав", show_alert=True)
        return
    if str(employee.role) != "ADMIN" and (not hasattr(employee.role, 'value') or employee.role.value != "ADMIN"):
        logging.warning(f"service_admin_delete: пользователь {user_id} имеет роль {employee.role}, требуется ADMIN")
        await callback.answer("Нет прав", show_alert=True)
        return
    
    service_id = int(callback.data.split(":")[1])
    service = await get_service(service_id)
    if not service:
        await callback.answer("Услуга не найдена", show_alert=True)
        return
    await state.set_state(ServiceEdit.confirm_delete)
    await state.update_data(service_id=service_id)
    await callback.message.edit_text(
        f"⚠️ Вы действительно хотите удалить услугу '{service.name}'?\n"
        f"Это действие нельзя отменить. Все заказы с этой услугой останутся в истории.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, удалить", callback_data="service_admin_delete_confirm")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="service_admin_delete_cancel")]
        ])
    )
    await callback.answer()
