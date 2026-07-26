from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional

def building_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🏢 Строение 1", callback_data="obj_building:1")],
        [InlineKeyboardButton(text="🏢 Строение 2", callback_data="obj_building:2")],
        [InlineKeyboardButton(text="🚗 Паркинг", callback_data="obj_parking")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="obj_cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def entrance_keyboard(building_id: int, entrances: List[int]) -> InlineKeyboardMarkup:
    buttons = []
    for e in entrances:
        buttons.append([InlineKeyboardButton(text=f"🚪 Подъезд {e}", callback_data=f"obj_entrance:{building_id}:{e}")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data="obj_back_building")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="obj_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def floor_keyboard(building_id: int, entrance: int, floors: List[int]) -> InlineKeyboardMarkup:
    buttons = []
    for f in floors:
        buttons.append([InlineKeyboardButton(text=f"🏗 Этаж {f}", callback_data=f"obj_floor:{building_id}:{entrance}:{f}")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data="obj_back_entrance")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="obj_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def apartment_keyboard(building_id: int, entrance: int, floor: int, apartments: List[int]) -> InlineKeyboardMarkup:
    buttons = []
    for apt in apartments:
        buttons.append([InlineKeyboardButton(text=f"Квартира {apt}", callback_data=f"obj_apartment:{building_id}:{entrance}:{floor}:{apt}")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data="obj_back_floor")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="obj_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def parking_floor_keyboard(building_id: int, floors: List[int]) -> InlineKeyboardMarkup:
    buttons = []
    for f in floors:
        label = f"Парковка {f} этаж" if f >= 0 else f"Парковка {-f} подземный"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"obj_parking_floor:{building_id}:{f}")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data="obj_back_building")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="obj_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def parking_spot_keyboard(building_id: int, floor: int, spots: List[int]) -> InlineKeyboardMarkup:
    buttons = []
    for spot in spots[:20]:
        buttons.append([InlineKeyboardButton(text=f"🚗 Место {spot}", callback_data=f"obj_parking_spot:{building_id}:{floor}:{spot}")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data="obj_back_parking_floor")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="obj_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def cellar_keyboard(building_id: int, cellars: List[int]) -> InlineKeyboardMarkup:
    buttons = []
    for cellar in cellars[:20]:
        buttons.append([InlineKeyboardButton(text=f"🔐 Келлер {cellar}", callback_data=f"obj_cellar:{building_id}:{cellar}")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data="obj_back_building")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="obj_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def location_type_keyboard(include_parking: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🏠 Квартира", callback_data="loc_type:apartment")],
        [InlineKeyboardButton(text="🏢 Общая зона", callback_data="loc_type:common_area")],
        [InlineKeyboardButton(text="🛗 Лифт", callback_data="loc_type:elevator")],
        [InlineKeyboardButton(text="🚪 Дверь", callback_data="loc_type:door")],
        [InlineKeyboardButton(text="📹 Камера", callback_data="loc_type:camera")],
        [InlineKeyboardButton(text="💡 Освещение", callback_data="loc_type:lighting")],
        [InlineKeyboardButton(text="🪟 Окно", callback_data="loc_type:window")],
        [InlineKeyboardButton(text="📦 Другое", callback_data="loc_type:other")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="obj_cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def parking_type_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🚗 Машиноместо", callback_data="parking_type:parking_spot")],
        [InlineKeyboardButton(text="📦 Келлер", callback_data="parking_type:cellar")],
        [InlineKeyboardButton(text="🚪 Ворота", callback_data="parking_type:gate")],
        [InlineKeyboardButton(text="🚧 Шлагбаум", callback_data="parking_type:barrier")],
        [InlineKeyboardButton(text="💡 Освещение", callback_data="parking_type:lighting")],
        [InlineKeyboardButton(text="🚰 Водоснабжение", callback_data="parking_type:water")],
        [InlineKeyboardButton(text="📹 Камера", callback_data="parking_type:camera")],
        [InlineKeyboardButton(text="📦 Другое", callback_data="parking_type:other")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="obj_cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
