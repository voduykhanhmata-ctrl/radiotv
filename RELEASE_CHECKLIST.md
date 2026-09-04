# Checklist công bố RadioTV 0.1.0

## Kiểm tra tự động

- Chạy `tools/validate.py` bằng Python x64 và x86 trên cùng bản nguồn.
- Kiểm tra smoke HLS và MP3 bằng backend thật, âm lượng 0; ghi rõ kiến trúc và thời điểm.
- So khớp SHA-256 của BASS/BASSHLS với PROVENANCE.md.
- Dựng addon và source ZIP, kiểm tra CRC và độ lặp lại của hash.
- Không đưa `work/`, `vendor/`, dữ liệu người dùng, token hoặc gói cũ vào Git.
- Kiểm tra gốc Git là chính thư mục radiotv-mit trước mọi thao tác thêm file.

## Người dùng nghiệm thu trên NVDA thật — còn chờ

- Cài bản ứng viên; Windows+Alt+V mở cửa sổ, Escape dừng/đóng, mở lại không lệch ô tìm kiếm.
- Tab/Shift+Tab, Ctrl+Tab, Ctrl+1..4, tìm không dấu, chọn nhóm/kênh và F1.
- Enter phát; Space phát/dừng; trái/phải đổi kênh; đổi nhanh rồi dừng không phát lại yêu cầu cũ.
- Khi duyệt một kênh khác, trạng thái vẫn đọc đúng kênh đang phát.
- Lưu yêu thích/âm lượng, khởi động lại NVDA; xác nhận giọng đọc và focus.
- Thử nguồn hỏng, mất mạng, lịch EPG không tải được; NVDA vẫn nhận bàn phím.

## Trước công bố — còn chờ

- Người duyệt độc lập xác nhận provenance và phạm vi so sánh; kết quả tự động không thay thế bước này.
- Chủ dự án xác nhận điều kiện phân phối BASS/BASSHLS phù hợp.
- Xác định URL kho GitHub đích, duyệt bản nguồn và ghi chú 0.1.0.
- Chỉ commit/push/tạo Release khi chủ dự án chỉ định. CI hiện chỉ tạo artifact ứng viên.


## Cập nhật công bố mã nguồn — 2026-09-04

Chủ dự án đã yêu cầu đối chiếu tính độc lập/phím tắt và tạo kho GitHub mới để đăng mã nguồn.
Kho đích: https://github.com/voduykhanhmata-ctrl/radiotv. Phiên bản 0.1.0 được ghi là bản thử nghiệm.
Năm phím toàn cục không trùng snapshot FreeRadio; các phím trong cửa sổ dùng quy ước quen thuộc.
Xem reports/INDEPENDENCE_AND_SHORTCUTS_2026-09-04.md để biết phương pháp và giới hạn.
Chưa xác nhận nghiệm thu NVDA thật hoặc review của người độc lập; không đổi trạng thái các bước đó thành hoàn tất.
