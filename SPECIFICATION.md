# Đặc tả chức năng RadioTV 0.1

Đây là đặc tả hành vi, không phải mô tả triển khai của phần mềm cũ.

## Chức năng bắt buộc

- Add-on NVDA chạy trên Windows 10/11, mục tiêu NVDA 2024.1 trở lên.
- Giao diện bàn phím gồm bốn tab: TV, Radio, Bóng đá, Yêu thích.
- Tìm kiếm tên/tag không phụ thuộc dấu tiếng Việt.
- Category lấy trực tiếp từ dữ liệu, không suy đoán bằng tên hoặc UUID.
- Enter phát nguồn đang chọn; trái/phải chuyển nguồn và tự phát.
- Space phát hoặc dừng; Escape đóng cửa sổ và dừng; F1 mở Help cục bộ.
- Phím toàn cục: Win+Alt+V, Win+Alt+P, Win+Alt+S, Win+Alt+Up/Down.
- Favorites và âm lượng được lưu bền vững, kiểm tra schema và ghi nguyên tử.
- Nhật ký riêng trong thư mục cấu hình NVDA, xoay file và khử credentials/token URL.
- Playback bất đồng bộ; yêu cầu mới nhất thắng, stop phải hủy yêu cầu đang chờ.
- Backend âm thanh chạy tách khỏi tiến trình NVDA; crash không làm NVDA crash.
- Sau crash khi đang phát, supervisor khởi động lại đúng một lần và phát lại URL
  cùng âm lượng; nếu thất bại phải báo rõ và không lặp vô hạn.
- Chỉ báo thành công khi backend xác nhận trạng thái phát, không dựa vào HTTP 200.

## Không thuộc 0.1

Recording, podcast, audiobook, time-shift, effects, bass mix, ffmpeg, tìm kiếm
Internet động, cập nhật tự động và tài khoản người dùng.

## Tiêu chí nghiệm thu

- Test pure-Python đạt trên Python x64 và x86; Python chỉ dùng để test, không đóng gói trong addon.
- Test protocol gồm correlation ID, timeout, cancel, crash và replay.
- Gói có LICENSE, notices, Help vi/en; không có cache, report hoặc dependency cấm.
- NVDA thật xác nhận mở/đóng, focus, Help, tìm kiếm, favorites, volume và playback.
- Ít nhất một HLS và một MP3 được `playback-confirmed`; các nguồn khác không được
  quảng bá là hoạt động nếu chưa kiểm tra.

Bản 0.1 chỉ phát âm thanh của kênh TV; chưa có video renderer. Danh mục bóng đá tĩnh.
Âm lượng hiện mở lại nguồn; bằng chứng test tự động không thay thế nghiệm thu NVDA thật.
