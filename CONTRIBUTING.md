# Đóng góp cho RadioTV

Đọc AGENTS.md, SPECIFICATION.md, CLEAN_ROOM_POLICY.md và PROVENANCE.md trước khi sửa.
Không dùng mã/kiến trúc/đoạn diff từ FreeRadio hoặc RadioTV cũ để triển khai.
Mã mới dùng SPDX LGPL-2.1-or-later và ghi tác giả phù hợp; dependency giữ giấy phép riêng.

Chạy `python -B tools/validate.py` trên x64 và x86 trước khi dựng gói.
Thêm kiểm thử tái hiện cho lỗi phát, cancel/crash, dữ liệu hoặc lưu cấu hình.
Không ép bộ test nạp library.zip của NVDA. Kiểm tra wx/NVDA thật là bước riêng.

Khi cập nhật danh mục, xem bản xem trước trước khi dùng `--write`.
Không thêm cookie, khóa DRM hoặc header tùy ý. Không coi HTTP 200 là bằng chứng phát.
Nếu nguồn có tham số token/chữ ký, giữ đầu vào trong `work/` được Git bỏ qua,
dùng `tools/public_catalog.py INPUT OUTPUT` tạo snapshot công khai rồi kiểm thử snapshot đó.
Công cụ chỉ phát hiện một số dạng tham số; người duyệt vẫn phải kiểm tra URL có bí mật trong đường dẫn.
`curate_vietnam_catalog.py` là migration lịch sử, chỉ cho xem trước để tránh ghi đè các sửa đổi sau đó.

Khi báo lỗi, ghi phiên bản NVDA/Windows, kiến trúc, tên hoặc ID kênh, thao tác tái hiện và trạng thái.
Không gửi URL có token, cookie hoặc file cấu hình riêng. Nhật ký RadioTV ở thư mục cấu hình NVDA/radiotv.
