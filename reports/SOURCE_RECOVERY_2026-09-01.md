# Khôi phục nguồn radio cũ — 2026-09-01

## Kết quả

- VOV Giao thông Hà Nội: URL cũ phát lại được sau khi cập nhật backend.
- VOV English 24/7 và VOV5 World Radio: thay bằng endpoint từ trang VOVWorld;
  cả hai vào trạng thái `playing`.
- VOH FM 99.9, FM 95.6, FM 87.7 và AM 610: thay bằng endpoint đang được trang
  radio VOH chính thức công bố; cả bốn vào trạng thái `playing`.
- XONE FM: URL cũ lỗi; endpoint nhúng trên trang XONE cũng không phát. Giữ tắt.
- VSBet: URL cũ lỗi và không xác định được nguồn chính thức hợp lệ. Giữ tắt.

## Xác minh

Audit catalog x64 đạt 7/7 nguồn được phục hồi. Worker x86 phát thật được VOV
English 24/7 và VOH FM 99.9. Kiểm tra chạy ở âm lượng 0, chỉ event backend
`playing` được tính; báo cáo không lưu URL.

Nguồn tham chiếu: trang radio chính thức VOH và VOVWorld. Nội dung âm thanh không
được đóng gói trong add-on.
