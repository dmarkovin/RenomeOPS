def get_location_type_name(loc_type):
    if not loc_type:
        return "—"
    mapping = {
        "apartment": "🏠 Квартира",
        "common_area": "🏢 Общая зона",
        "elevator": "🛗 Лифт",
        "other": "📦 Другое",
        "parking_spot": "🚗 Машиноместо",
        "cellar": "📦 Келлер",
        "gate": "🚪 Ворота",
        "barrier": "🚧 Шлагбаум",
        "lighting": "💡 Освещение",
        "water": "🚰 Водоснабжение",
        "camera": "📹 Камера",
        "parking": "🚗 Паркинг",
    }
    return mapping.get(loc_type, loc_type)
