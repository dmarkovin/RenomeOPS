from typing import Dict, List, Tuple

# Данные по объекту
OBJECT_DATA = {
    1: {  # Корпус 1
        "name": "Новослободская 24астр1",
        "entrances": {
            1: {"floors": 5, "apartments_per_floor": 4, "apartment_start": 1, "apartment_end": 16}
        },
        "parking_floors": [-1],  # только -1 этаж
        "cellars": 35,  # количество келлеров
    },
    2: {  # Корпус 2
        "name": "Новослободская 24астр2",
        "entrances": {
            1: {"floors": 10, "apartments_per_floor": 4, "apartment_start": 1, "apartment_end": 34},
            2: {"floors": 10, "apartments_per_floor": 6, "apartment_start": 35, "apartment_end": 79},
            3: {"floors": 10, "apartments_per_floor": 6, "apartment_start": 80, "apartment_end": 130},
        },
        "parking_floors": [-1, -2],  # -1 и -2 этажи
        "cellars": 35,
    }
}

def get_buildings() -> List[Tuple[int, str]]:
    """Список корпусов"""
    return [(b_id, data["name"]) for b_id, data in OBJECT_DATA.items()]

def get_entrances(building_id: int) -> List[int]:
    """Список подъездов для корпуса"""
    return list(OBJECT_DATA[building_id]["entrances"].keys())

def get_floors(building_id: int, entrance: int) -> List[int]:
    """Список этажей для подъезда"""
    return list(range(1, OBJECT_DATA[building_id]["entrances"][entrance]["floors"] + 1))

def get_apartments(building_id: int, entrance: int, floor: int) -> List[int]:
    """Список квартир на этаже"""
    data = OBJECT_DATA[building_id]["entrances"][entrance]
    per_floor = data["apartments_per_floor"]
    start = data["apartment_start"] + (floor - 1) * per_floor
    end = start + per_floor - 1
    return list(range(start, end + 1))

def get_parking_floors(building_id: int) -> List[int]:
    """Список этажей паркинга"""
    return OBJECT_DATA[building_id]["parking_floors"]

def get_parking_spots(building_id: int, floor: int) -> List[int]:
    """Список машиномест на этаже"""
    if building_id == 1:
        # -1 этаж: 1-114
        return list(range(1, 115))
    else:
        # -1 этаж: 1-114, -2 этаж: 115-213
        if floor == -1:
            return list(range(1, 115))
        else:
            return list(range(115, 214))

def get_cellars(building_id: int) -> List[int]:
    """Список келлеров (общее количество)"""
    return list(range(1, OBJECT_DATA[building_id]["cellars"] + 1))
