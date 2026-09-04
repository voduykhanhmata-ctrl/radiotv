# RadioTV 0.1

RadioTV là add-on NVDA để nghe radio và âm thanh của các kênh TV, thể thao bằng bàn phím.
Tác giả: **Võ Duy Khánh**. Mã của dự án dùng **LGPL-2.1-or-later**; BASS/BASSHLS có điều khoản riêng.
Tên thư mục `radiotv-mit` là tên lịch sử, không phải giấy phép hiện hành.

Kho mã nguồn: [voduykhanhmata-ctrl/radiotv](https://github.com/voduykhanhmata-ctrl/radiotv).
Bản **0.1.0** được công bố dưới dạng **bản thử nghiệm**. Kiểm tra NVDA thực tế và
review provenance bởi người độc lập còn được theo dõi trong [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md).
CI kiểm thử mỗi thay đổi; việc tạo bản phát hành do chủ dự án quyết định.

## Chức năng

- Bốn mục: TV, Radio, Bóng đá, Yêu thích; 23 nhóm TV.
- Tìm tên/thẻ tiếng Việt có dấu hoặc không dấu; duyệt danh sách không tự phát.
- Lưu kênh yêu thích và âm lượng trong thư mục cấu hình NVDA.
- Tải lịch XMLTV ở nền, thử làm mới sau 6 giờ khi tra cứu; thử lại sau 5 phút nếu lỗi.
- Phát qua tiến trình PowerShell riêng với BASS/BASSHLS; có Windows Media Runtime dự phòng.
- Hủy yêu cầu cũ khi đổi kênh hoặc dừng; thử phục hồi tối đa một lần nếu tiến trình đã phát bị crash.
- Nhật ký có giới hạn dung lượng, không ghi URL, User-Agent, token hoặc nội dung trả về tự do từ worker.

## Phím tắt

| Phím | Chức năng |
|---|---|
| Windows+Alt+V | Mở RadioTV |
| Windows+Alt+P | Phát hoặc dừng |
| Windows+Alt+S | Dừng |
| Windows+Alt+Lên/Xuống | Tăng/giảm âm lượng 5% |
| Tab / Shift+Tab | Di chuyển giữa các điều khiển |
| Ctrl+Tab / Ctrl+Shift+Tab | Mục kế tiếp / trước |
| Ctrl+PageDown / Ctrl+PageUp | Mục kế tiếp / trước |
| Ctrl+1..4 | TV / Radio / Bóng đá / Yêu thích |
| Enter trong danh sách | Phát kênh đã chọn |
| Space trong danh sách | Phát hoặc dừng |
| Trái / Phải trong danh sách | Kênh trước / sau và phát |
| Escape | Dừng và đóng cửa sổ |
| F1 | Trợ giúp cục bộ |

## Giới hạn của 0.1

- Chỉ có âm thanh; chưa có cửa sổ hiển thị video. Phát/dừng không phải tạm dừng để nghe tiếp đúng vị trí.
- Thay đổi âm lượng hiện mở lại luồng nên có thể ngắt tiếng ngắn.
- Giao diện tiếng Việt; có Help tiếng Việt và tiếng Anh, chưa có bản dịch giao diện khác.
- Danh mục đóng gói tĩnh: 786 mục, gồm 595 TV, 30 radio, 161 thể thao; 784 mục được bật.
  Danh sách bóng đá có thể hết hạn. Có tên trong danh mục không có nghĩa đang phát được.
- 46 URL chứa tham số xác thực/chữ ký đã được giữ lại ở bản sao cục bộ, không đưa vào bản công khai.
  Một mục trong kho nguồn chưa hỗ trợ cũng được tách ra. Không xóa tham số để tạo URL giả.
- Không có recording, podcast, time-shift, FFmpeg, tự cập nhật danh mục hoặc xử lý DRM.
- Mạng, codec hệ điều hành và nguồn phát quyết định khả năng mở kênh. Mốc `playback-confirmed`
  chỉ là bằng chứng tại thời điểm ghi, không phải bảo đảm kênh còn hoạt động.

## Cài đặt và kiểm thử

Mục tiêu: Windows 10/11, NVDA 2024.1 trở lên. Manifest giữ mốc NVDA 2026.2.1 từ đợt trước;
bản sửa lần này cần nghiệm thu lại theo checklist. Chưa xác nhận Windows ARM64.

Tải `RadioTV-0.1.0.nvda-addon` tại [bản thử nghiệm 0.1.0](https://github.com/voduykhanhmata-ctrl/radiotv/releases/tag/v0.1.0), rồi mở bằng NVDA để cài. Khi tự dựng, file nằm trong `dist/`.
Để phát triển, dùng Python 3.11; thư viện chuẩn đủ cho kiểm thử không giao diện.
wxPython phải khớp với Python khi kiểm tra cửa sổ, không thêm `library.zip` của NVDA khác phiên bản vào đường dẫn import.

Chạy bằng cả Python x64 và x86, cùng thư mục đầu ra (thay đường dẫn bằng Python thực tế):

```powershell
& 'C:\path\to\python-x64.exe' -B tools/validate.py
& 'C:\path\to\python-x86.exe' -B tools/validate.py
python -B tools/build_dev_package.py
python -B tools/build_dev_package.py --source
```

Bộ đóng gói từ chối bằng chứng thiếu, lỗi hoặc cũ so với nội dung nguồn hiện tại.
CI GitHub chạy hai kiến trúc và tạo artifact để kiểm tra, không tự push hoặc phát hành.
Các bài kiểm tra wx được báo là bỏ qua nếu wxPython không có; đây không phải nghiệm thu giao diện.

## Cấu trúc

```text
globalPlugins/radiotv/
  nvda_plugin.py       tích hợp NVDA và phím tắt
  core/                dữ liệu, tìm kiếm, cấu hình, XMLTV
  ui/                  trạng thái giao diện và cửa sổ wx
  audio/               giao thức, quản lý tiến trình, worker PowerShell
  support/             trợ giúp, nhật ký
  runtime/x64,x86/     BASS và BASSHLS của Un4seen
data/                  danh mục và schema
doc/vi,en/             trợ giúp cục bộ
tests/                 kiểm thử
tools/                 nhập danh mục, audit, kiểm thử và đóng gói
.github/workflows/     kiểm thử CI
```

Xem [ARCHITECTURE.md](ARCHITECTURE.md), [PROVENANCE.md](PROVENANCE.md),
[LICENSING.md](LICENSING.md), [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
và [CONTRIBUTING.md](CONTRIBUTING.md).

## Quan hệ với FreeRadio

Dự án có chung mục đích nghe radio trong NVDA. Hồ sơ của dự án mô tả quá trình viết mới
theo đặc tả và dữ liệu do chủ dự án cung cấp. Kiểm tra tương đồng tự động chỉ là một nguồn
bằng chứng; không xác nhận tuyệt đối nguồn gốc hay quyền sở hữu toàn bộ mã.
Xem [đối chiếu mã và phím tắt](reports/INDEPENDENCE_AND_SHORTCUTS_2026-09-04.md),
báo cáo rà soát trong `reports/REVIEW_0.1_2026-09-04.md` và chính sách clean-room.
