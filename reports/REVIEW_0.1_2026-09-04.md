# Rà soát RadioTV 0.1 — 04/09/2026

## Kết luận

RadioTV hiện có kiến trúc tách dữ liệu, controller, giao diện wx và tiến trình âm thanh.
Dự án có chung mục đích nghe radio với FreeRadio. Phép đo trong phạm vi bên dưới
không tìm thấy bằng chứng file Python trùng hoặc khối hàm trùng từ 80 token.
Không cần đổi tên lớp, đảo mã hoặc làm biến dạng code để giảm độ tương đồng.
Mã đã được sửa vì lỗi chức năng và yêu cầu chuẩn bị phát hành.

Phiên bản thống nhất là **0.1.0**; mã dự án dùng **LGPL-2.1-or-later** theo quyết định
đã ghi ngày 01/09. Thư mục `radiotv-mit` giữ nguyên tên. BASS/BASSHLS là thành phần
có giấy phép riêng; gói cài đặt không phải toàn bộ phần mềm đều thuộc LGPL.

## Phạm vi đọc và kiểm tra

Đã đọc mã Python/PowerShell trong globalPlugins, tools, tests; tài liệu, manifest,
schema/danh mục và hồ sơ nguồn gốc. Đã đối chiếu SHA-256 bốn DLL với provenance.
Không kiểm toán được mã nội bộ DLL đóng của Un4seen. Không mở mã cũ trong ngữ cảnh sửa code.

Luồng chính: phím tắt NVDA → controller → supervisor → worker PowerShell → BASS/HLS
hoặc Windows Media Runtime. Worker gửi trạng thái JSON; controller chuyển snapshot về UI.
Catalog dùng category tường minh và tìm không dấu; cấu hình ghi nguyên tử; XMLTV tải nền.

## Lỗi và thay đổi

| Mức | Phát hiện | Cách xử lý |
|---|---|---|
| Cao | Sự kiện phát/lỗi đến trước khi controller giữ request ID bị bỏ qua | Tạo ID trước, giữ sự kiện đến sớm và không ghi đè trạng thái đã xác nhận |
| Cao | Popen/ghi lệnh chạy trên luồng gọi UI | Đưa khởi chạy sang thread nền, hủy yêu cầu cũ và thu hồi tiến trình bị bỏ dở |
| Cao | Error/ended/malformed message có thể để worker còn sống | Kết thúc và thu hồi worker; giới hạn dòng giao thức; test crash lặp/cancel/terminal |
| Cao | State JSON là list gây TypeError ngoài ProtocolError | Kiểm tra kiểu version/state/code/detail, chặn URL và ký tự điều khiển trong lỗi |
| Cao | Bộ test nạp library.zip NVDA khác Python, gây bad magic number dây chuyền | Bỏ sửa sys.path vào cài đặt NVDA; dùng runtime khớp, báo rõ khi bỏ qua wx |
| Cao | Build không bắt buộc test hai kiến trúc và phiên bản ghi nhiều chỗ | Lấy version từ manifest; bằng chứng x64/x86 phải khớp hash bản nguồn |
| Vừa | Space chỉ phát; duyệt kênh làm trạng thái gọi sai kênh đang nghe | Space toggle; trạng thái dùng kênh đang phát; sửa ô tìm kiếm khi mở lại |
| Vừa | Chuyển tab có thể thông báo hai lần; phát lỗi ngoài cửa sổ thiếu phản hồi | ChangeSelection và thông báo kết quả playback qua NVDA |
| Vừa | XMLTV tải/giải nén không giới hạn, giữ cache mãi | Giới hạn dung lượng, từ chối DTD/entity, làm mới khi tra cứu và đủ thời gian |
| Vừa | Thiếu nhật ký riêng theo đặc tả | Log có rotation, chỉ ghi trạng thái/replay, không ghi URL hoặc chi tiết tùy ý |
| Vừa | URL sai cổng/bracket hoặc ký tự điều khiển có thể lọt/raise sai loại lỗi | Hàm kiểm tra URL chung, lỗi không in URL, timestamp có timezone |
| Vừa | Nhập playlist trống có thể xóa toàn bộ nhóm nhập trước | Từ chối snapshot rỗng; validate trước khi ghi nguyên tử; giữ User-Agent bóng đá |
| Vừa | Migration 30/08 có thể ghi đè sửa chữa mới hơn | Công cụ lịch sử chỉ cho xem trước |
| Vừa | README/Help hứa video, pause, bóng đá realtime, ổn định tuyệt đối | Viết lại theo chức năng đã triển khai, ghi rõ giới hạn |
| Phát hành | Repo chưa có .git riêng và dữ liệu có URL ký/token | Chuẩn bị kho riêng; tách dữ liệu ký/token vào bản sao cục bộ, bổ sung .gitignore |

## Dữ liệu công khai

Bản gốc có 832 mục. Đã giữ lại cục bộ 46 mục có token/chữ ký (37 TV, 9 thể thao),
không sửa URL bằng cách bỏ tham số. Một mục tương tự trong kho chưa hỗ trợ cũng được giữ lại.
Snapshot công khai có 786 mục: 595 TV, 30 radio, 161 thể thao; 784 bật.
Vẫn có 23 nhóm TV, 21 nguồn SCTV tương thích và danh mục radio. Hai mục tắt lịch sử là XONE và VSBet.
Đây là snapshot tĩnh, không phải cam kết mọi kênh đang phát được.

## So sánh với FreeRadio

Chương trình chỉ xuất số liệu tổng hợp, không tên file/hàm hoặc đoạn mã cũ.
Phạm vi: 16 file Python mới; snapshot FreeRadio 12 file trong Git index cục bộ,
RadioTV cũ 11 file trong globalPlugins. Cả ba tập parse thành công.

| Chỉ số | FreeRadio | RadioTV cũ |
|---|---:|---:|
| File trùng byte | 0 | 0 |
| Cửa sổ 80 token trùng trong hàm đủ dài | 0 | 0 |
| Cửa sổ sau chuẩn hóa tên/literal | 0 | 0 |

Loại khỏi đo: DLL, dữ liệu, import, hằng module, hàm ngắn. Chỉ so các snapshot có sẵn;
không bao quát mọi phiên bản FreeRadio trên Internet. Không thể từ số liệu này suy ra
“không giống 100%”, “sở hữu toàn bộ mã” hoặc kết luận pháp lý. Cần review provenance độc lập.

## Kiểm chứng và việc còn lại

- Kiểm thử tự động x64/x86 được ghi bằng `tools/validate.py`; báo cáo máy ở `work/validation/`.
- Kiểm tra wx thật bị bỏ qua nếu môi trường không có wxPython. Các test keyboard routing giả lập
  chỉ kiểm tra cách gọi lệnh, không xác nhận focus hay giọng đọc trên NVDA.
- Smoke thực tế VOV1 (HLS) và RFI Việt (MP3) đạt `playing` trên cả x64/x86, âm lượng 0.
  Lượt trong môi trường hạn chế bị lỗi truy cập; thử lại với quyền truy cập bình thường đã đạt.
  Chưa thử lại toàn bộ 786 nguồn. Trạng thái xác minh lịch sử trong catalog được giữ nguyên.
- Bốn DLL khớp hash đã ghi; package dựng bằng danh sách file cho phép, kiểm tra CRC và hash lặp lại.
- Còn chờ người dùng nghiệm thu NVDA và người duyệt độc lập xác nhận provenance/điều kiện phân phối.
- Chưa có URL kho GitHub đích được chủ dự án chỉ định; chưa commit, push hoặc tạo GitHub Release.

Nguồn đối chiếu: [API BASS_ChannelIsActive](https://www.un4seen.com/doc/bass/BASS_ChannelIsActive.html),
[điều khoản BASS](https://www.un4seen.com/bass.html),
[NVDA GlobalPlugin API](https://github.com/nvaccess/nvda/blob/master/source/globalPluginHandler.py).
