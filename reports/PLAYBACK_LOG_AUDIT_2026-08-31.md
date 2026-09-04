# Kiểm tra lỗi phát từ nhật ký NVDA — 2026-08-31

> Đây là báo cáo lịch sử trước khi cập nhật backend. Nguồn MMA và các nguồn
> Tinhlagi từng lỗi hiện không còn bị tự động ẩn; xem
> `PLAYBACK_COMPATIBILITY_2026-09-01.md`.

## Kết quả xác minh

- Add-on đang chạy: RadioTV `0.1.0-dev1`.
- Lỗi phát RadioTV duy nhất được ghi trong `nvda.log` hiện tại xảy ra lúc
  `09:26:59`: `MMA-TV.com`, `stream_open_failed: 41`.
- Không có lỗi phát RadioTV nào khác trong `nvda.log` hoặc `nvda-old.log`.
- MMA-TV.com là mục mới có ID `tl-mma-tv-com-5f18e7e2`; danh mục trước đó không
  có URL cũ cho kênh này.
- Nguồn M3U có hai lần xuất hiện MMA-TV.com nhưng cả hai dùng cùng một URL, nên
  không có URL tương thích dự phòng khác để thử.

## Xử lý

- Tạm ẩn riêng MMA-TV.com và đánh dấu `failed` với thời điểm/mã lỗi thực tế.
- Bộ nhập giữ trạng thái tạm ẩn qua những lần nhập lại nếu URL vẫn không đổi.
- Nếu nhà cung cấp thay URL trong lần nhập sau, URL mới không kế thừa lỗi cũ và
  có thể được thử lại.
- Không thay đổi KIX HD hoặc các kênh không có lỗi trong nhật ký.
