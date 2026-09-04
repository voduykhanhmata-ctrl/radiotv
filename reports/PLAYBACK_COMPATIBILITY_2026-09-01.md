# Khả năng phát SCTV và nguồn từng bị ẩn — 2026-09-01

## Kết quả

- SCTV HLS tương thích: 21/21 phát thật trên worker x64.
- Phim Sự Kiện: 43/43 phát thật trên worker x64.
- Worker x86: SCTV3 phát bằng BASS; nguồn Thỏ Ơi phát bằng Windows Media Runtime
  sau khi BASS dừng trước trạng thái phát.
- Nguồn từ danh mục Tinhlagi đang bị ẩn: 0.
- SCTV15, SCTV17 và SCTV22 là DASH/DRM: không đưa vào danh sách phát, không lưu
  khóa và không đóng gói hồ sơ nguồn không tương thích.

## Thay đổi tạo ra kết quả

- BASS x64/x86 được cập nhật từ 2.4.18.3 lên 2.4.18.23.
- Chỉ dẫn User-Agent hợp lệ của từng kênh được chuyển qua worker thay vì bị bỏ.
- Bật chế độ playlist mạng của BASS.
- Khi BASS không mở URL bọc, worker giải quyết một chuyển hướng HTTP an toàn rồi
  thử lại URL đích; việc này sửa manifest tương đối của SCTV3 và các kênh cùng loại.
- Nếu BASS không mở hoặc dừng trước `playing`, worker thử một lần bằng Windows
  Media Runtime có sẵn trong hệ điều hành.
- Audit lỗi không còn tự ẩn nguồn; nguồn được giữ trong giao diện ở trạng thái
  chưa xác minh để có thể thử lại khi máy chủ thay đổi.

## Tiêu chuẩn và bằng chứng

HTTP 200 không được tính là phát được. Chỉ event `playing` từ backend thật mới
được tính. Audit chạy ở âm lượng 0 và báo cáo không ghi URL luồng.

- `sctv_playback_audit_2026-09-01.json`: 21 kết quả `playing`.
- `event_playback_audit_2026-09-01.json`: 43 kết quả `playing`.
- 56 kiểm thử đơn vị đạt trên Python x64; hai đường phát đại diện đạt trên worker
  PowerShell x86.

## Nguồn radio cũ

Bảy nguồn cũ đã được kiểm tra lại và phục hồi: VOV Giao thông Hà Nội, VOV
English 24/7, VOV5 World Radio, VOH FM 99.9, VOH FM 95.6, VOH FM 87.7 và VOH
AM 610. Sáu URL lỗi được thay bằng endpoint mà trang chính thức VOV/VOH đang
công bố. XONE FM và VSBet tiếp tục tắt vì cả URL cũ lẫn endpoint công khai tìm
được đều không vào trạng thái `playing`.

Không thêm FFmpeg, BASS_AAC, bass_fx hoặc bassmix. BASS_AAC đã bị loại sau khi
kiểm tra nghĩa vụ GPL; đường dự phòng hiện dùng thành phần có sẵn trong Windows.
