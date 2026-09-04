# Chính sách clean-room

## Phạm vi được phép

Dự án mới được xây từ:

1. Yêu cầu chức năng do Võ Duy Khánh cung cấp.
2. Danh sách tên/URL đài do Võ Duy Khánh tự thu thập.
3. Tài liệu chính thức của NVDA, Python, Windows và backend âm thanh được chọn.
4. Mã và kiểm thử được viết mới trong `radiotv-mit`.

## Phạm vi bị cách ly

Không dùng mã, comment, tên nội bộ, cấu trúc lớp, giao thức hoặc test từ FreeRadio
và RadioTV cũ. Project cũ chỉ được dùng ở cổng cuối để máy đo tương đồng; người
triển khai không sửa mã mới dựa trên kết quả từng đoạn.

## Dữ liệu đài

Ngày 2026-08-30, người dùng xác nhận danh sách nguồn đài trong RadioTV cũ do
chính họ tìm và yêu cầu tái sử dụng. Chỉ các fact sau được chuyển: mã định danh,
tên hiển thị, URL, quốc gia, tag và category. Không chuyển code bao quanh dữ liệu.

Mỗi lần kiểm tra nguồn phải lưu thời điểm và mức bằng chứng:

- `unverified`: chưa kiểm tra trong lượt hiện tại;
- `reachable`: máy chủ phản hồi, chưa chứng minh phát được;
- `playback-confirmed`: backend thật đã xác nhận phát;
- `failed`: backend thật không phát được, kèm lỗi đã khử token.

## Cổng phát hành nguồn mở

Mã do dự án viết dùng `LGPL-2.1-or-later`. Chỉ xem xét phát hành khi không còn code/file từ dự án cũ, dependency có nguồn và
điều khoản rõ ràng, kiểm tra tương đồng không phát hiện khối đáng kể, và một người
review độc lập xác nhận provenance. Đây là biện pháp kỹ thuật, không thay thế tư
vấn pháp lý khi có tranh chấp.
