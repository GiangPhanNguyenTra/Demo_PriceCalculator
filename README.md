# PoC Demo: Tính giá cước dưới 3 giây

Đây là một ứng dụng demo Proof of Concept (PoC) đơn giản nhằm mục đích chứng minh khả năng tính toán giá cước nhanh chóng cho một hệ thống đặt xe (ride-hailing).

## 🎯 Mục tiêu PoC

Mục tiêu chính của PoC này là:

1.  **Chứng minh hiệu năng:** Khả năng xử lý và tính toán giá cước cho một lô lớn các chuyến đi (ví dụ: 10000 chuyến) kết thúc đồng thời trong **thời gian dưới 3 giây** trong điều kiện hoạt động bình thường.
2.  **Mô phỏng tính giá động:** Áp dụng các yếu tố ảnh hưởng đến giá cước một cách linh hoạt cho từng chuyến đi, bao gồm:
    - **Cung cầu (Supply-Demand):** ±15% dựa trên tình hình tài xế/khách hàng.
    - **Thời tiết (Weather):** +0-10% khi thời tiết xấu.
    - **Tắc đường (Congestion):** +0-12% dựa trên mức độ ùn tắc.
    - **Khách hàng Trung thành (Loyalty):** -10-0% cho người dùng thân thiết.
3.  **Trực quan hóa:** Cung cấp giao diện web đơn giản để thực hiện các bài test và hiển thị kết quả một cách rõ ràng.

## ✨ Tính năng Demo

- **Test Hàng Loạt (Bulk Test):**
  - Cho phép nhập số lượng chuyến đi cần mô phỏng (ví dụ: 100, 1000, 10000).
  - Tạo dữ liệu chuyến đi giả lập (ID, khoảng cách, loại xe, trạng thái khách hàng thân thiết) với các yếu tố giá **ngẫu nhiên cho từng chuyến**.
  - Sử dụng `concurrent.futures.ThreadPoolExecutor` để xử lý tính toán giá song song, tối ưu hóa thời gian phản hồi.
  - Hiển thị **toàn bộ** kết quả chi tiết (ID, khoảng cách, giá gốc, giá cuối cùng, lý do thay đổi, thời gian tính toán riêng).
  - Hiển thị thống kê tổng hợp (tổng số chuyến, tổng thời gian xử lý, thời gian trung bình/chuyến, **kết luận PoC thành công/thất bại** dựa trên mốc 3 giây).
- **Test Chuyến Đơn Lẻ (Single Trip Test):**
  - Cho phép nhập thông tin chi tiết của một chuyến đi (khoảng cách, loại xe).
  - Cho phép chọn **mức độ (1-10)** cho từng yếu tố ảnh hưởng (Cung cầu, Thời tiết, Tắc đường, Trung thành).
  - Hiển thị giá cước cơ bản, giá cước cuối cùng và các yếu tố cụ thể đã được áp dụng.
- **Hiển thị Tham số:** Hiển thị các cấu hình giá cơ bản (giá mở cửa, giá/km cho từng loại xe) và biên độ ảnh hưởng của các yếu tố.

## 🛠️ Công nghệ sử dụng

- **Backend:** Python 3, Flask
- **Frontend:** HTML, CSS, JavaScript (Fetch API)
