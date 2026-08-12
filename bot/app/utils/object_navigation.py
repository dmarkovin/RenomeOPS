from typing import Dict, List, Tuple, Union

# Общие зоны для первого этажа (каждая зона имеет уникальный ID внутри подъезда)
COMMON_AREAS = {
    "building1_entrance1": [
        (1, "Ресепшен"),
        (2, "Лобби"),
        (3, "Санузел"),
        (4, "Лифтовой холл"),
        (5, "Лифты"),
        (6, "Колясочная"),
        (7, "Входной тамбур, двери"),
        (8, "Выход в сторону эвакуационной лестницы")
    ],
    "building2_entrance1": [
        (1, "Ресепшен"),
        (2, "Лобби"),
        (3, "Лифтовой холл"),
        (4, "Лифты"),
        (5, "Санузел"),
        (6, "Стафф-рум"),
        (7, "Колясочная"),
        (8, "Входной тамбур, двери"),
        (9, "Выход в сторону эвакуационной лестницы")
    ],
    "building2_entrance2": [
        (1, "Центральный ресепшен"),
        (2, "Kid's Lab"),
        (3, "Fit Lab"),
        (4, "Санузел"),
        (5, "Лифтовой холл"),
        (6, "Лифты"),
        (7, "Стафф-рум"),
        (8, "Кабинет управляющего"),
        (9, "Лобби"),
        (10, "Колясочная"),
        (11, "Входной тамбур, двери")
    ],
    "building2_entrance3": [
        (1, "Центральный ресепшен"),
        (2, "Kid's Lab"),
        (3, "Fit Lab"),
        (4, "Санузел"),
        (5, "Лифтовой холл"),
        (6, "Лифты"),
        (7, "Стафф-рум"),
        (8, "Кабинет управляющего"),
        (9, "Лобби"),
        (10, "Колясочная"),
        (11, "Входной тамбур, двери")
    ]
}

def get_common_areas(building_id: int, entrance: int) -> List[Tuple[int, str]]:
    key = f"building{building_id}_entrance{entrance}"
    return COMMON_AREAS.get(key, [])

def get_common_area_name(building_id: int, entrance: int, area_id: int) -> str:
    areas = get_common_areas(building_id, entrance)
    for aid, name in areas:
        if aid == area_id:
            return name
    return None

OBJECT_DATA = {
    1: {  # Корпус 1 (Новослободская 24астр1)
        "name": "Новослободская 24астр1",
        "entrances": {
            1: {
                "floors": 5,
                "apartments": {
                    1: [1, 2, 3, 4, 5, 6, 7, 8],
                    2: [1, 2, 3, 4],
                    3: [5, 6, 7, 8],
                    4: [9, 10, 11, 12],
                    5: [13, 14, 15, 16],
                }
            }
        },
        "parking_floors": [-1],
        "cellars": 35,
    },
    2: {  # Корпус 2 (Новослободская 24астр2)
        "name": "Новослободская 24астр2",
        "entrances": {
            1: {
                "floors": 10,
                "apartments": {
                    1: [1, 2, 3, 4, 5, 6, 7, 8, 9],
                    2: [1, 2, 3, 4],
                    3: [5, 6, 7, 8],
                    4: [9, 10, 11, 12],
                    5: [13, 14, 15, 16],
                    6: [17, 18, 19, 20],
                    7: [21, 22, 23, 24],
                    8: [25, 26, 27, 28],
                    9: [29, 30, 31, 32],
                    10: [33, 34],
                }
            },
            2: {
                "floors": 10,
                "apartments": {
                    1: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                    2: [35, 36, 37, 38, 39, 40],
                    3: [41, 42, 43, 44, 45, 46],
                    4: [47, 48, 49, 50, 51],
                    5: [52, 53, 54, 55, 56],
                    6: [57, 58, 59, 60, 61],
                    7: [62, 63, 64, 65, 66],
                    8: [67, 68, 69, 70, 71],
                    9: [72, 73, 74, 75, 76],
                    10: [77, 78, 79],
                }
            },
            3: {
                "floors": 10,
                "apartments": {
                    1: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                    2: [80, 81, 82, 83, 84, 85, 86],
                    3: [87, 88, 89, 90, 91, 92, 93],
                    4: [94, 95, 96, 97, 98, 99, 100],
                    5: [101, 102, 103, 104, 105, 106],
                    6: [107, 108, 109, 110, 111],
                    7: [112, 113, 114, 115, 116],
                    8: [117, 118, 119, 120, 121],
                    9: [122, 123, 124, 125, 126],
                    10: [127, 128, 129, 130],
                }
            }
        },
        "parking_floors": [-1, -2],
        "cellars": 35,
    }
}

def get_buildings() -> List[Tuple[int, str]]:
    return [(b_id, data["name"]) for b_id, data in OBJECT_DATA.items()]

def get_entrances(building_id: int) -> List[int]:
    return list(OBJECT_DATA[building_id]["entrances"].keys())

def get_floors(building_id: int, entrance: int) -> List[int]:
    data = OBJECT_DATA[building_id]["entrances"][entrance]
    return list(data["apartments"].keys())

def get_apartments(building_id: int, entrance: int, floor: int) -> List[Union[int, str]]:
    data = OBJECT_DATA[building_id]["entrances"][entrance]
    items = data["apartments"].get(floor, [])
    return items

def get_parking_floors(building_id: int) -> List[int]:
    return OBJECT_DATA[building_id]["parking_floors"]

def get_parking_spots(building_id: int, floor: int) -> List[int]:
    if building_id == 1:
        return list(range(1, 115))
    else:
        if floor == -1:
            return list(range(1, 115))
        else:
            return list(range(115, 214))

def get_cellars(building_id: int) -> List[int]:
    return list(range(1, OBJECT_DATA[building_id]["cellars"] + 1))
