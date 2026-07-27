from aiogram.types import ReplyKeyboardRemove
from app.handlers.services.user import ServiceOrderState
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from app.utils.object_navigation import (
    get_buildings, get_entrances, get_floors, get_apartments,
    get_parking_floors, get_parking_spots, get_cellars
)
from app.keyboards.object_navigation import (
    building_keyboard, entrance_keyboard, floor_keyboard,
    apartment_keyboard, parking_floor_keyboard, parking_spot_keyboard,
    cellar_keyboard
)

router = Router()

@router.callback_query(F.data.startswith("obj_"))
async def handle_object_navigation(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state == ServiceOrderState.select_object:
        return
    data = callback.data.split(":")
    action = data[0]

    if action == "obj_building":
        building_id = int(data[1])
        entrances = get_entrances(building_id)
        await callback.message.edit_text(
            f"🏢 Выберите подъезд для корпуса {building_id}:",
            reply_markup=entrance_keyboard(building_id, entrances)
        )

    elif action == "obj_entrance":
        building_id = int(data[1])
        entrance = int(data[2])
        floors = get_floors(building_id, entrance)
        await callback.message.edit_text(
            f"🏗 Выберите этаж для подъезда {entrance} (корпус {building_id}):",
            reply_markup=floor_keyboard(building_id, entrance, floors)
        )

    elif action == "obj_floor":
        building_id = int(data[1])
        entrance = int(data[2])
        floor = int(data[3])
        apartments = get_apartments(building_id, entrance, floor)
        await callback.message.edit_text(
            f"🏠 Выберите квартиру на {floor} этаже (подъезд {entrance}):",
            reply_markup=apartment_keyboard(building_id, entrance, floor, apartments)
        )

    elif action == "obj_apartment":
        building_id = int(data[1])
        entrance = int(data[2])
        floor = int(data[3])
        apartment = int(data[4])
        # Сохраняем результат в состоянии
        result = {
            "building": building_id,
            "entrance": entrance,
            "floor": floor,
            "apartment": apartment,
            "type": "apartment"
        }
        await state.update_data(object_selection=result)
        await callback.message.edit_text(
            f"✅ Выбрана квартира {apartment} (корпус {building_id}, подъезд {entrance}, этаж {floor})"
        )
        # Здесь можно завершить выбор или передать управление другому хендлеру

    elif action == "obj_parking_floor":
        building_id = int(data[1])
        floor = int(data[2])
        spots = get_parking_spots(building_id, floor)
        await callback.message.edit_text(
            f"🅿️ Выберите машиноместо на этаже {floor}:",
            reply_markup=parking_spot_keyboard(building_id, floor, spots)
        )

    elif action == "obj_parking_spot":
        building_id = int(data[1])
        floor = int(data[2])
        spot = int(data[3])
        result = {
            "building": building_id,
            "parking_floor": floor,
            "parking_spot": spot,
            "type": "parking"
        }
        await state.update_data(object_selection=result)
        await callback.message.edit_text(
            f"✅ Выбрано машиноместо {spot} (этаж {floor})"
        )

    elif action == "obj_cellar":
        building_id = int(data[1])
        cellar = int(data[2])
        result = {
            "building": building_id,
            "cellar": cellar,
            "type": "cellar"
        }
        await state.update_data(object_selection=result)
        await callback.message.edit_text(
            f"✅ Выбран келлер {cellar}"
        )

    elif action == "obj_back_building":
        await callback.message.edit_text(
            "🏢 Выберите корпус:",
            reply_markup=building_keyboard()
        )

    elif action == "obj_back_entrance":
        # Для простоты возврат к выбору корпуса
        await callback.message.edit_text(
            "🏢 Выберите корпус:",
            reply_markup=building_keyboard()
        )

    elif action == "obj_back_floor":
        await callback.message.edit_text(
            "🏢 Выберите корпус:",
            reply_markup=building_keyboard()
        )

    elif action == "obj_back_parking_floor":
        await callback.message.edit_text(
            "🏢 Выберите корпус:",
            reply_markup=building_keyboard()
        )

    elif action == "obj_cancel":
        await callback.message.delete()
        await callback.answer("Действие отменено")
        await state.clear()

    await callback.answer()
