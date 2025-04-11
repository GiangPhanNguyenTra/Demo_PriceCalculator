import random
import time
import math # Cần cho làm tròn

# --- Cấu hình giá cước và yếu tố ---
BASE_FARE = 10000
PRICE_PER_KM = {
    "motorbike": 10000, # Cập nhật giá theo yêu cầu mới
    "4seater": 14000,
    "7seater": 18000,
}
VEHICLE_TYPES = list(PRICE_PER_KM.keys())

# Biên độ ảnh hưởng của các yếu tố (Giữ nguyên biên độ min/max)
FACTOR_RANGES = {
    "supply_demand": (-0.15, 0.15), # Cung cầu
    "weather": (0.0, 0.10),         # Thời tiết (Bắt đầu từ 0 để level 1 có thể là 0%)
    "congestion": (0.0, 0.12),      # Tắc đường (Bắt đầu từ 0)
    "loyalty": (-0.10, -0.00),       # Trung thành (Level 1 giảm nhiều nhất, Level 10 giảm ít nhất)
}

# Tỷ lệ khách hàng thân thiết giả định trong batch test
LOYALTY_RATIO = 0.2 # 20%

FACTOR_NAMES_VI = {
    "supply_demand": "Cung cầu",
    "weather": "Thời tiết",
    "congestion": "Tắc đường",
    "loyalty": "Trung thành"
}

def get_factor_value(factor_name, level=None):
    """
    Lấy giá trị factor ngẫu nhiên (nếu level=None) hoặc theo mức độ 1-10.
    """
    if factor_name not in FACTOR_RANGES:
        return 0.0

    min_val, max_val = FACTOR_RANGES[factor_name]

    if level is not None:
        # Đảm bảo level nằm trong khoảng 1-10
        level = max(1, min(10, int(level)))
        # Nội suy tuyến tính giá trị dựa trên level
        # Level 1 -> min_val, Level 10 -> max_val
        # Ngoại trừ Loyalty: Level 1 -> min_val (giảm nhiều nhất), Level 10 -> max_val (giảm ít nhất)
        # Công thức: value = min + (max - min) * (level - 1) / (10 - 1)
        factor_value = min_val + (max_val - min_val) * (level - 1) / 9.0
        return factor_value
    else:
        # Tạo giá trị ngẫu nhiên trong khoảng cho bulk test
        return random.uniform(min_val, max_val)


def calculate_single_trip_price(trip_data):
    """
    Tính giá cho một chuyến đi duy nhất. Yếu tố được lấy từ trip_data.

    Args:
        trip_data (dict): Chứa 'trip_id', 'distance', 'vehicle_type', 'is_loyal',
                          và các 'factor_name_factor' (ví dụ: 'supply_demand_factor').

    Returns:
        tuple: (base_price, final_price, reasons list, calc_duration_ms)
    """
    start_calc_time = time.perf_counter()

    distance = trip_data['distance']
    vehicle_type = trip_data['vehicle_type']
    is_loyal = trip_data.get('is_loyal', False)

    if vehicle_type not in PRICE_PER_KM:
        raise ValueError(f"Loại xe không hợp lệ: {vehicle_type}")

    # 1. Tính giá cơ bản
    price_km = PRICE_PER_KM[vehicle_type]
    base_price = BASE_FARE + (price_km * distance)
    final_price = base_price
    reasons = []

    # 2. Áp dụng các yếu tố đã được tạo sẵn cho chuyến đi này
    sd_factor = trip_data.get('supply_demand_factor', 0)
    # Chỉ thêm lý do nếu factor có ảnh hưởng (khác 0 một chút)
    if not math.isclose(sd_factor, 0, abs_tol=1e-9):
        final_price *= (1 + sd_factor)
        reasons.append(f"{FACTOR_NAMES_VI['supply_demand']} ({sd_factor*100:+.1f}%)")

    weather_factor = trip_data.get('weather_factor', 0)
    if weather_factor > 1e-9: # Chỉ áp dụng nếu > 0
        final_price *= (1 + weather_factor)
        reasons.append(f"{FACTOR_NAMES_VI['weather']} (+{weather_factor*100:.1f}%)")

    congestion_factor = trip_data.get('congestion_factor', 0)
    if congestion_factor > 1e-9: # Chỉ áp dụng nếu > 0
        final_price *= (1 + congestion_factor)
        reasons.append(f"{FACTOR_NAMES_VI['congestion']} (+{congestion_factor*100:.1f}%)")

    # Áp dụng Loyalty nếu là khách hàng TT và có yếu tố loyalty âm
    loyalty_factor = trip_data.get('loyalty_factor', 0)
    if is_loyal and loyalty_factor < -1e-9:
        final_price *= (1 + loyalty_factor) # loyalty_factor là số âm
        reasons.append(f"{FACTOR_NAMES_VI['loyalty']} ({loyalty_factor*100:.1f}%)") # Hiển thị dấu âm

    # 3. Làm tròn giá (ví dụ: đến nghìn đồng gần nhất)
    final_price = round(final_price / 1000) * 1000

    end_calc_time = time.perf_counter()
    calc_duration_ms = (end_calc_time - start_calc_time) * 1000

    # Đảm bảo giá cuối cùng không âm
    final_price = max(0, final_price)

    return base_price, final_price, reasons, calc_duration_ms
