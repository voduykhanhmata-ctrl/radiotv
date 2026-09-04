# Quy tắc dự án RadioTV clean-room

## Mục tiêu

Viết mới hoàn toàn add-on RadioTV 0.1; giấy phép hiện hành là LGPL-2.1-or-later theo quyết định đã ghi ngày 2026-09-01 trong PROVENANCE.md. Dự án này không phải refactor,
fork hoặc bản dịch của FreeRadio hay `D:\work page\radiotv`.

## Hàng rào bắt buộc

- Không đọc, chép, dịch, sửa lại hoặc mô phỏng mã nguồn FreeRadio/RadioTV cũ.
- Không nhận diff, đoạn mã, tên lớp/hàm hoặc kiến trúc từ dự án cũ làm ngữ cảnh.
- Chỉ dùng `SPECIFICATION.md`, tài liệu API chính thức và các file được tạo mới
  trong project này để triển khai.
- Ngoại lệ duy nhất là dữ liệu đài trong `data/stations.json`. Người dùng xác
  nhận đây là danh sách URL do chính họ thu thập và cho phép tái sử dụng.
- Không sao chép comment, thứ tự mã, quy tắc phân loại hoặc cấu trúc Python của
  file chứa dữ liệu cũ. Dữ liệu mới phải có schema trung lập và category tường minh.
- Không lấy DLL BASS từ FreeRadio/RadioTV cũ. Nếu chọn BASS, phải tải bản mới từ
  nhà cung cấp chính thức và ghi nguồn/hash/điều khoản trong provenance.
- Không thêm FFmpeg, `bass_fx.dll`, `bassmix.dll`, recording, podcast hoặc time-shift.

## Chất lượng

- Logic catalog/storage/protocol phải test được mà không cần NVDA hoặc wxPython.
- UI không được chặn khi mở nguồn; mọi thao tác dài chạy ngoài UI thread.
- Không coi HTTP 200 là bằng chứng phát được. Chỉ ghi “phát được” sau khi backend
  thật xác nhận trạng thái phát.
- Không build package khi test x64/x86 chưa đạt.
- Mọi AI bên ngoài chỉ được nhận file clean-room cụ thể, không được quét workspace.

## Giấy phép và provenance

- Mã do dự án này tạo mới dùng SPDX `LGPL-2.1-or-later` và copyright Võ Duy Khánh.
- Thành phần/dữ liệu bên thứ ba giữ giấy phép riêng và phải được ghi trong
  `THIRD_PARTY_NOTICES.md` trước khi đưa vào package.
- Cập nhật `PROVENANCE.md` khi thêm nguồn dữ liệu, dependency hoặc tài liệu API.
