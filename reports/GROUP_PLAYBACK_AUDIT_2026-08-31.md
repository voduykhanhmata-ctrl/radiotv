# Audit phát thật: Phim Sự Kiện và SCTV — 2026-08-31

> Báo cáo lịch sử này đã được thay thế bởi kết quả ngày 2026-09-01 sau khi cập
> nhật BASS và thêm đường phát dự phòng. Xem `PLAYBACK_COMPATIBILITY_2026-09-01.md`.

## Phương pháp

- Backend: BASS/BASSHLS x64 giống đường phát của add-on.
- Âm lượng kiểm tra: 0 để không gây tiếng chồng lên NVDA.
- Chỉ trạng thái `playing` của backend được tính là phát được.
- Báo cáo không ghi URL luồng.

## Kết quả

- Phim Sự Kiện: 26/43 mục phát được; 17 mục lỗi `stream_open_failed: 41`.
- SCTV nguồn chính: 5/20 kênh phát được.
- 15 SCTV lỗi được rà theo tên kênh trong danh sách nguồn.
- Chín SCTV cũ có một URL khác để thử; chỉ URL dự phòng của SCTV19 phát được.
- Sau xử lý, nhóm SCTV còn 6 kênh hoạt động: SCTV1, SCTV5, SCTV10,
  SCTV14, SCTV19 và SCTV4K.
- 31 mục lỗi không có nguồn dự phòng phát được đã được tạm ẩn: 17 Phim Sự
  Kiện và 14 SCTV.

## Nhóm “Báo”

Danh mục không có nhóm tên “Báo”. Nhóm gần nhất là `📰 Tin Tức`; tại thời điểm
kiểm tra không có tên kênh Việt Nam rõ ràng trong nhóm này. Vì chưa xác định được
đúng kênh người dùng muốn xóa, audit không xóa mục nào khỏi nhóm Tin Tức.

## Tệp bằng chứng máy đọc được

- `playback_audit_event_sctv_2026-08-31.json`
- `sctv_fallback_audit_2026-08-31.json`
