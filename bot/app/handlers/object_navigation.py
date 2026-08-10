from aiogram.types import ReplyKeyboardRemove
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
    data = callback.data.split(":")
    action = data[0]
    current_state = await state.get_state()

    # Разрешаем навигацию для состояний создания задач и услуг
    # Проверяем, что состояние существует и относится к TaskCreate или ServiceOrderState
    if current_state:
        # Если состояние не связано с созданием задачи или услуги, запрещаем
        if not ("TaskCreate" in current_state or "ServiceOrderState" in current_state):
            await callback.answer("Действие недоступно", show_alert=True)
            return
    else:
        # Если состояния нет, тоже запрещаем
        await callback.answer("Действие недоступно", show_alert=True)
        return

    # Получаем сохранённые данные из состояния
    state_data = await state.get_data()
    building = state_data.get("building")
    entrance = state_data.get("entrance")
    floor = state_data.get("floor")
    object_type = state_data.get("object_type")  # "apartment", "parking", "cellar"

    if action == "obj_building":
        building_id = int(data[1])
        await state.update_data(building=building_id)
        entrances = get_entrances(building_id)
        await state.update_data(object_type="apartment")
        await callback.message.edit_text(
            f"🏢 Выберите подъезд для корпуса {building_id}:",
            reply_markup=entrance_keyboard(building_id, entrances)
        )

    elif action == "obj_entrance":
        building_id = int(data[1])
        entrance_num = int(data[2])
        await state.update_data(entrance=entrance_num)
        floors = get_floors(building_id, entrance_num)
        await callback.message.edit_text(
            f"🏗 Выберите этаж для подъезда {entrance_num} (корпус {building_id}):",
            reply_markup=floor_keyboard(building_id, entrance_num, floors)
        )

    elif action == "obj_floor":
        building_id = int(data[1])
        entrance_num = int(data[2])
        floor_num = int(data[3])
        await state.update_data(floor=floor_num)
        apartments = get_apartments(building_id, entrance_num, floor_num)
        if not apartments:
            await callback.message.edit_text("На этом этаже нет квартир. Выберите другой этаж.")
            return
        await callback.message.edit_text(
            f"🏠 Выберите квартиру на {floor_num} этаже (подъезд {entrance_num}):",
            reply_markup=apartment_keyboard(building_id, entrance_num, floor_num, apartments)
        )

    elif action == "obj_apartment":
        building_id = int(data[1])
        entrance_num = int(data[2])
        floor_num = int(data[3])
        apartment_num = int(data[4])
        result = {
            "building": building_id,
            "entrance": entrance_num,
            "floor": floor_num,
            "apartment": apartment_num,
            "type": "apartment"
        }
        await state.update_data(object_selection=result)
        await callback.message.edit_text(
            f"✅ Выбрана квартира {apartment_num} (корпус {building_id}, подъезд {entrance_num}, этаж {floor_num})"
        )
        # Здесь можно завершить выбор или передать управление другому хендлеру

    elif action == "obj_parking":
        await state.update_data(object_type="parking")
        await callback.message.edit_text(
            "🚗 Выберите уровень паркинга:",
            reply_markup=parking_floor_keyboard(2, [-1, -2])
        )

    elif action == "obj_parking_floor":
        building_id = int(data[1])
        floor_num = int(data[2])
        await state.update_data(parking_floor=floor_num)
        spots = get_parking_spots(building_id, floor_num)
        await callback.message.edit_text(
            f"🚗 Выберите машиноместо на этаже {floor_num}:",
            reply_markup=parking_spot_keyboard(building_id, floor_num, spots)
        )

    elif action == "obj_parking_spot":
        building_id = int(data[1])
        floor_num = int(data[2])
        spot_num = int(data[3])
        result = {
            "building": building_id,
            "parking_floor": floor_num,
            "parking_spot": spot_num,
            "type": "parking"
        }
        await state.update_data(object_selection=result)
        await callback.message.edit_text(
            f"✅ Выбрано машиноместо {spot_num} (этаж {floor_num})"
        )

    elif action == "obj_cellar":
        building_id = int(data[1])
        cellar_num = int(data[2])
        result = {
            "building": building_id,
            "cellar": cellar_num,
            "type": "cellar"
        }
        await state.update_data(object_selection=result)
        await callback.message.edit_text(
            f"✅ Выбран келлер {cellar_num}"
        )

    # ========== ОБРАБОТЧИКИ КНОПОК "НАЗАД" ==========
    elif action == "obj_back_building":
        await callback.message.edit_text(
            "🏢 Выберите корпус:",
            reply_markup=building_keyboard()
        )

    elif action == "obj_back_entrance":
        if building:
            entrances = get_entrances(building)
            await callback.message.edit_text(
                f"🏢 Выберите подъезд для корпуса {building}:",
                reply_markup=entrance_keyboard(building, entrances)
            )
        else:
            await callback.message.edit_text(
                "🏢 Выберите корпус:",
                reply_markup=building_keyboard()
            )

    elif action == "obj_back_floor":
        if building and entrance:
            floors = get_floors(building, entrance)
            await callback.message.edit_text(
                f"🏗 Выберите этаж для подъезда {entrance} (корпус {building}):",
                reply_markup=floor_keyboard(building, entrance, floors)
            )
        else:
            await callback.message.edit_text(
                "🏢 Выберите корпус:",
                reply_markup=building_keyboard()
            )

    elif action == "obj_back_parking_floor":
        if building:
            await callback.message.edit_text(
                "🚗 Выберите уровень паркинга:",
                reply_markup=parking_floor_keyboard(2, [-1, -2])
            )
        else:
            await callback.message.edit_text(
                "🏢 Выберите корпус:",
                reply_markup=building_keyboard()
            )

    elif action == "obj_cancel":
        await callback.message.delete()
        await callback.answer("Действие отменено")
        await state.clear()

    await callback.answer()
