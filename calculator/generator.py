import random
import uuid
from .pricing import VEHICLE_TYPES, LOYALTY_RATIO, FACTOR_RANGES, get_factor_value # Thêm FACTOR_RANGES, get_factor_value

def generate_trips(num_trips):
    """
    Tạo danh sách các chuyến đi giả, mỗi chuyến có yếu tố ngẫu nhiên riêng.
    """
    trips = []
    for i in range(num_trips):
        is_loyal_customer = random.random() < LOYALTY_RATIO
        trip = {
            "trip_id": f"trip_{i+1:04d}_{str(uuid.uuid4())[:4]}", # ID dễ đọc hơn
            "distance": round(random.uniform(1.0, 45.0), 1),
            "vehicle_type": random.choice(VEHICLE_TYPES),
            "is_loyal": is_loyal_customer,
            # Tạo yếu tố ngẫu nhiên cho từng chuyến đi
            "supply_demand_factor": get_factor_value("supply_demand"),
            "weather_factor": get_factor_value("weather"),
            "congestion_factor": get_factor_value("congestion"),
            # Tạo sẵn yếu tố loyalty tiềm năng (sẽ chỉ áp dụng nếu is_loyal=True)
            "loyalty_factor": get_factor_value("loyalty")
        }
        trips.append(trip)
    return trips