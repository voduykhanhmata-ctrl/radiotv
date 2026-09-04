# Thay đổi

## 0.1.0 — 2026-09-04, bản ứng viên đưa mã nguồn lên GitHub

- Khởi động tiến trình phát ở nền; giữ sự kiện phát/lỗi đến sớm bằng request ID được tạo trước.
- Thu hồi worker sau lỗi/kết thúc, chặn sự kiện cũ, chỉ replay crash một lần.
- Siết kiểu dữ liệu giao thức, URL, timestamp; chặn message quá lớn và ký tự điều khiển.
- Sửa Space phát/dừng, tên kênh đang phát, ô tìm kiếm khi mở lại và thông báo chuyển tab lặp.
- Giới hạn tải/giải nén XMLTV, có thời hạn làm mới, thêm nhật ký dung lượng giới hạn.
- Sửa bộ test làm nhiễm đường dẫn import với NVDA khác Python.
- Ngăn danh sách nhập trống xóa kênh cũ; kiểm tra dữ liệu trước khi ghi nguyên tử;
  giữ User-Agent của nguồn bóng đá và xử lý lỗi runner audit rõ ràng.
- Bản công khai giữ 786 mục; 46 nguồn có token/chữ ký và một mục chưa hỗ trợ được giữ cục bộ.
- Đồng bộ LGPL và 0.1.0; sửa mô tả video/tạm dừng/danh sách cập nhật tự động chưa được triển khai.
- Thêm CI hai kiến trúc, source ZIP và cổng đóng gói buộc bằng chứng khớp bản nguồn.

Nghiệm thu NVDA thật và duyệt provenance độc lập cho bản này còn chờ theo RELEASE_CHECKLIST.md.
