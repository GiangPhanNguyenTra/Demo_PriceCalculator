import time
from flask import Flask, render_template, request, jsonify
from concurrent.futures import ThreadPoolExecutor

# Import các hàm/biến cần thiết từ pricing và generator
from calculator.pricing import (
    calculate_single_trip_price,
    get_factor_value, # Cần cho single test
    BASE_FARE,
    PRICE_PER_KM,
    FACTOR_RANGES,
    VEHICLE_TYPES
)
from calculator.generator import generate_trips

app = Flask(__name__)

# --- THÊM ĐỊNH NGHĨA FILTER VÀO ĐÂY ---
@app.template_filter('format_price')
def format_price_filter(value):
    """Định dạng số thành chuỗi tiền tệ VND."""
    try:
        # Cố gắng chuyển thành số nguyên trước khi định dạng
        num = int(value)
        # Sử dụng f-string formatting với dấu phẩy ngăn cách hàng nghìn
        # và thay thế dấu phẩy bằng dấu chấm cho chuẩn VND
        return f"{num:,}".replace(',', '.')
    except (ValueError, TypeError):
        # Nếu không phải số hoặc lỗi, trả về giá trị gốc
        return value
# --- KẾT THÚC PHẦN THÊM ---

executor = ThreadPoolExecutor(max_workers=8) # Giữ nguyên executor

def process_trip_wrapper(trip_data):
    """
    Hàm bao bọc để tính giá cho một chuyến đi (đã có sẵn factors).
    """
    try:
        # Gọi hàm tính giá mới, chỉ cần trip_data
        base_price, final_price, reasons, calc_time = calculate_single_trip_price(trip_data)
        return {
            "trip_id": trip_data["trip_id"],
            "distance": trip_data["distance"],
            "vehicle_type": trip_data["vehicle_type"],
            "base_price": base_price,
            "final_price": final_price,
            "reasons": reasons,
            "calc_time_ms": calc_time,
            "error": None
        }
    except Exception as e:
        print(f"Error processing trip {trip_data.get('trip_id')}: {e}")
        return {
            "trip_id": trip_data.get("trip_id", "N/A"),
            "distance": trip_data.get("distance", 0),
            "vehicle_type": trip_data.get("vehicle_type", "N/A"),
            "base_price": 0,
            "final_price": 0,
            "reasons": ["Error processing"],
            "calc_time_ms": 0,
            "error": str(e)
        }

@app.route('/')
def index():
    params = {
        "base_fare": BASE_FARE,
        "price_per_km": PRICE_PER_KM,
        "factor_ranges": FACTOR_RANGES,
        "vehicle_types": VEHICLE_TYPES # Truyền thêm loại xe cho single test dropdown
    }
    # Giờ đây template 'index.html' có thể sử dụng filter 'format_price'
    return render_template('index.html', params=params)

@app.route('/calculate_bulk', methods=['POST'])
def calculate_bulk():
    try:
        num_trips = int(request.form.get('num_trips', 0))
        if num_trips <= 0:
            return jsonify({"error": "Số lượng chuyến không hợp lệ"}), 400

        start_time = time.perf_counter()

        # 1. Tạo dữ liệu chuyến đi (đã bao gồm factors ngẫu nhiên cho mỗi chuyến)
        trips_data = generate_trips(num_trips)

        # 3. Sử dụng ThreadPoolExecutor để tính toán song song
        results = list(executor.map(process_trip_wrapper, trips_data))

        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        avg_time_ms = total_time_ms / num_trips if num_trips > 0 else 0

        valid_results = [r for r in results if r['error'] is None]

        stats = {
            "num_trips": num_trips,
            "processed_ok": len(valid_results),
            "processed_error": len(results) - len(valid_results),
            "total_time_ms": total_time_ms,
            "avg_time_ms": avg_time_ms,
        }

        return jsonify({"results": valid_results, "stats": stats})

    except ValueError:
        return jsonify({"error": "Số lượng chuyến phải là số nguyên"}), 400
    except Exception as e:
        print(f"Server error during bulk calculation: {e}")
        return jsonify({"error": f"Lỗi server: {e}"}), 500


@app.route('/calculate_single', methods=['POST'])
def calculate_single():
    try:
        distance = float(request.form.get('distance'))
        vehicle_type = request.form.get('vehicle_type')
        sd_level = int(request.form.get('sd_level'))
        weather_level = int(request.form.get('weather_level'))
        congestion_level = int(request.form.get('congestion_level'))
        loyalty_level = int(request.form.get('loyalty_level'))

        if not all([distance, vehicle_type, sd_level, weather_level, congestion_level, loyalty_level]):
             return jsonify({"error": "Thiếu thông tin đầu vào"}), 400
        if not (1 <= sd_level <= 10 and 1 <= weather_level <= 10 and \
                1 <= congestion_level <= 10 and 1 <= loyalty_level <= 10):
             return jsonify({"error": "Mức độ yếu tố phải từ 1 đến 10"}), 400
        if distance <= 0:
             return jsonify({"error": "Khoảng cách phải lớn hơn 0"}), 400
        if vehicle_type not in VEHICLE_TYPES:
             return jsonify({"error": "Loại xe không hợp lệ"}), 400

        trip_data = {
            "trip_id": "single-test-" + str(time.time()),
            "distance": distance,
            "vehicle_type": vehicle_type,
            "is_loyal": True, # Giả định loyal trong single test
            "supply_demand_factor": get_factor_value("supply_demand", sd_level),
            "weather_factor": get_factor_value("weather", weather_level),
            "congestion_factor": get_factor_value("congestion", congestion_level),
            "loyalty_factor": get_factor_value("loyalty", loyalty_level)
        }

        base_price, final_price, reasons, _ = calculate_single_trip_price(trip_data)

        result = {
            "trip_id": trip_data["trip_id"],
            "distance": distance,
            "vehicle_type": vehicle_type,
            "base_price": base_price,
            "final_price": final_price,
            "reasons": reasons,
            "used_factors": {
                "Cung cầu": f"{trip_data['supply_demand_factor']*100:+.1f}% (Level {sd_level})",
                "Thời tiết": f"{trip_data['weather_factor']*100:+.1f}% (Level {weather_level})",
                "Tắc đường": f"{trip_data['congestion_factor']*100:+.1f}% (Level {congestion_level})",
                "Trung thành": f"{trip_data['loyalty_factor']*100:+.1f}% (Level {loyalty_level}, áp dụng nếu loyal)"
            }
        }
        return jsonify(result)

    except ValueError:
        return jsonify({"error": "Dữ liệu không hợp lệ (số, level...)"}), 400
    except Exception as e:
        print(f"Server error during single calculation: {e}")
        return jsonify({"error": f"Lỗi server: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)