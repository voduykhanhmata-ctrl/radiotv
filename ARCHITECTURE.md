# Kiến trúc RadioTV 0.1

`nvda_plugin.py` nhận phím tắt NVDA, khởi tạo catalog/controller và cửa sổ wx.
`ui/controller.py` giữ bộ lọc, kênh đang chọn, kênh đang phát, yêu thích và âm lượng.
`ui/main_window.py` chuyển thao tác bàn phím thành lệnh và đưa cập nhật nền về UI bằng `wx.CallAfter`.

## Dữ liệu

`core/entities.py` chứa entity bất biến và kiểm tra URL HTTP(S).
`catalog_service.py` kiểm tra schema, danh tính duy nhất, timestamp và tạo chỉ mục tìm kiếm không dấu.
`persistence.py` đọc/migrate cấu hình và dùng file tạm + fsync + replace để ghi nguyên tử.
`epg_service.py` tải XMLTV ở nền, giới hạn 16 MiB tải/32 MiB giải nén và từ chối DTD/entity.
Core không import NVDA, wx, subprocess hoặc ctypes. EPG có truy cập mạng qua urllib trong worker nền.

## Luồng phát

1. Controller tạo request ID và lưu trạng thái trước khi gọi supervisor, để không bỏ mất sự kiện đến sớm.
2. Supervisor hủy phiên cũ, tạo worker ở thread nền; thao tác khởi chạy tiến trình không nằm trên UI thread.
3. URL, âm lượng và User-Agent đi qua stdin JSON, không nằm trong dòng lệnh PowerShell.
4. Worker ưu tiên BASS 2.4.18.23 + BASSHLS 2.4.5; thử một chuyển hướng ban đầu và Windows Media Runtime nếu cần.
5. Giao thức đầu ra kiểm tra version, request ID, kiểu/trường/độ dài. Chỉ backend báo `playing` mới xác nhận phát.
6. `stop`, đổi kênh, lỗi giao thức hoặc kết thúc nguồn đều thu hồi tiến trình; crash sau khi phát chỉ được replay một lần.
7. Thời gian khởi động tối đa mặc định 60 giây, để đường dự phòng có thời gian chạy. Công cụ smoke có timeout riêng.

Âm lượng hiện khởi động lại nguồn. Chưa có giao thức thay đổi âm lượng tại chỗ, pause/resume hoặc video renderer.
`support/diagnostics.py` ghi trạng thái vào `radiotv/radiotv.log` trong thư mục cấu hình NVDA;
256 KiB/file, hai file dự phòng. Không ghi URL, token hay chi tiết tùy ý từ worker.

## Phát hành

`release_support.py` quy định danh sách file được đóng gói và băm nội dung nguồn.
`validate.py` tạo bằng chứng x64/x86. `build_dev_package.py` chỉ dựng archive khi cả hai khớp nguồn hiện tại.
Archive có timestamp/quyền file cố định, kiểm tra CRC; không chứa work, cache, vendor hoặc dữ liệu người dùng.
`public_catalog.py` giữ nguyên URL gốc trong đầu vào và xuất snapshot mới không chứa tham số nhạy cảm nhận diện được.
