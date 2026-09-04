# Phân công AI và người kiểm thử

## Codex — chủ trì

Giữ policy clean-room, thiết kế/viết code, tích hợp, kiểm thử hai kiến trúc, kiểm
tra lại mọi kết luận bên ngoài và quyết định file nào được thay đổi.

Đã hoàn tất M0–M2: policy/provenance, dữ liệu trung lập, catalog search và
persistence nguyên tử; 17/17 test đạt trên x64/x86.

## Freebuff — QA dữ liệu, lượt nhỏ

Chỉ đọc `data/stations.json`, schema và provenance. Tìm ID/URL trùng, trường thiếu,
category sai rõ ràng và nguồn HTTP/rủi ro. Không đọc project cũ, không sửa source,
summary dưới 700 ký tự. Chạy ở M1 và có thể lặp lại một lần trước M5.

M1 đã hoàn tất qua job `20260830-091035-cf7d0c`: không có lỗi nghiêm trọng;
finding duy nhất là test chưa khóa tên trùng. Codex đã bổ sung điều kiện này và
chạy lại 5/5 test trên x64/x86.

## Antigravity — review tổng hợp, một lượt

Chỉ nhận specification, architecture, protocol và test clean-room sau M3. Review
concurrency, cancel/crash, security/logging và ranh giới license trong một prompt;
không dùng cho việc nhỏ vì mỗi phiên có chi phí ngữ cảnh nền lớn.

## Người dùng — chủ dữ liệu và nghiệm thu NVDA

Xác nhận quyền đối với danh sách đài, thử bàn phím/focus/âm thanh trên NVDA thật,
quyết định backend/điều khoản phân phối và phê duyệt phát hành.

## Quy tắc chung

Không AI nào được tự commit, push, phát hành, cài dependency hoặc mở rộng context.
Trạng thái `completed` của agent không phải bằng chứng; Codex phải tái hiện bằng
test/file thực tế.
