# Lộ trình RadioTV 0.1

## Cập nhật 2026-09-04

Bản nguồn 0.1.0 đã được rà soát và sửa lỗi để chuẩn bị GitHub. Xem CHANGELOG.md,
reports/REVIEW_0.1_2026-09-04.md và RELEASE_CHECKLIST.md. Các mốc dưới đây là lịch sử;
trạng thái mới nhất chưa phải tuyên bố đã công bố hoặc nghiệm thu NVDA đầy đủ.

## M0 — Provenance và cách ly

Trạng thái: **Hoàn tất ngày 2026-08-30.**

Đầu ra: policy, specification, assignment, giấy phép nguồn mở. Cổng đạt khi mọi agent
chỉ nhận context trong project mới và project cũ không nằm trong prompt triển khai.

## M1 — Dữ liệu đài

Trạng thái: **Hoàn tất ngày 2026-08-30.**

Chuyển fact người dùng sở hữu sang `stations.json`; schema, 83 ID/tên/URL duy nhất,
category tường minh, trạng thái kiểm tra ban đầu `unverified`. Freebuff review độc
lập về duplicate, trường thiếu và rủi ro nguồn; Codex xác minh lại mọi finding.

## M2 — Core không phụ thuộc NVDA

Trạng thái: **Hoàn tất ngày 2026-08-30.**

Viết entities, catalog search và persistence mới. Test lỗi JSON, migration,
atomic write, accent search và category counts trên x64/x86.

## M3 — Playback vertical slice

Trạng thái: **Hoàn tất ngày 2026-08-30.**

Chọn backend từ tài liệu/giấy phép chính thức; tải dependency mới nếu cần. Viết
protocol, engine process, supervisor, timeout/cancel/crash replay. Xác nhận một
HLS và một MP3 trên x64/x86. Lượt gửi source cho Antigravity bị chặn
bởi cổng bảo mật; không vượt chặn và chờ người dùng phê duyệt rõ payload.

## M4 — NVDA UI

Trạng thái: **Bản dev đã viết và đã được người dùng cài/chạy thử trên NVDA thật;
vẫn tiếp tục nhận phản hồi về focus và bàn phím.**

Viết adapter NVDA/wx mới, keyboard/focus/Help/log. Test controller không cần wx,
sau đó kiểm tra thủ công bằng NVDA thật.

## M5 — Hardening và gói 0.1

Trạng thái: **Gói thử `0.1.0-dev6` đã qua cổng build sau thay đổi giấy phép và
phục hồi nguồn ngày 2026-09-01; chưa công bố.**

Chạy test x64/x86, scan secret/dependency/dead code, so sánh tương đồng ở mức file
và khối, render Help, build deterministic, kiểm tra CRC/hash. Cổng playback hiện
đạt 21/21 SCTV và 43/43 Phim Sự Kiện trên x64, cùng hai đường đại diện trên x86.
Chỉ phát hành sau review provenance, kiểm tra NVDA thực tế và build cuối.
