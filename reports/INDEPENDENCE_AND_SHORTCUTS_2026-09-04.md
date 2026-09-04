# Đối chiếu tính độc lập và phím tắt — 04/09/2026

## Kết luận trong phạm vi đã kiểm tra

Không phát hiện file Python trùng byte hoặc khối hàm trùng từ 80 token với hai snapshot tham chiếu.
Năm phím toàn cục RadioTV đều khác các khai báo phím của snapshot FreeRadio đang đối chiếu.
Không có căn cứ kỹ thuật trong các phép đo này để đổi tên lớp/hàm hoặc đảo thứ tự mã.
Đây là một lượt đối chiếu bổ sung bằng công cụ, không phải chứng nhận tác quyền hoặc review của một người thứ ba.

## Nguồn bằng chứng

- RadioTV: 16 file Python trong globalPlugins/radiotv, bản 0.1.0 tại thời điểm kiểm tra.
- FreeRadio: 12 file Python của snapshot trong Git index cục bộ; RadioTV cũ: 11 file Python.
- Đọc tham chiếu bên trong chương trình đo, không xuất đoạn mã, tên nội bộ hoặc kiến trúc cũ vào ngữ cảnh sửa mã.
- Kiểm tra keybindings chỉ xuất tổ hợp phím khai báo và nhãn phím trong Help dành cho người dùng.
- Cả ba tập Python parse thành công; file trùng: 0; cửa sổ 80 token trùng: 0;
  cửa sổ sau chuẩn hóa tên/literal: 0, đối với cả hai tập tham chiếu.

Phép đo loại import, dữ liệu, hằng ở cấp module, hàm ngắn và DLL. Nó không bao quát mọi phiên bản
FreeRadio trên Internet, mã chưa có trong snapshot hoặc nguồn gốc của dữ liệu. Phím do người dùng tự gán có thể khác.

## Đối chiếu phím tắt

| Lệnh toàn cục | RadioTV 0.1.0 | FreeRadio trong snapshot |
|---|---|---|
| Mở cửa sổ | Windows+Alt+V | Nhóm Ctrl+Windows; có Ctrl+Windows+R |
| Phát/dừng | Windows+Alt+P | Có Ctrl+Windows+P |
| Dừng | Windows+Alt+S | Có Ctrl+Windows+S |
| Tăng âm lượng | Windows+Alt+Lên | Có Ctrl+Windows+Lên |
| Giảm âm lượng | Windows+Alt+Xuống | Có Ctrl+Windows+Xuống |

Tổng cộng snapshot tham chiếu khai báo 15 tổ hợp có tiền tố kb:, đều thuộc họ Ctrl+Windows.
RadioTV khai báo 5 tổ hợp thuộc họ Windows+Alt. Giao của hai tập sau chuẩn hóa tên/phím bổ trợ là rỗng.
Mô tả hành động của bảng dùng chức năng RadioTV; cột FreeRadio chỉ xác nhận tổ hợp có trong khai báo.

Ở phạm vi cửa sổ, vẫn có các phím giống nhau: Enter, Space, Escape, F1, Ctrl+Tab,
Ctrl+Shift+Tab và các nhãn Ctrl+1..4. Giống tổ hợp không đồng nghĩa giống hành vi hoặc sao chép code.
RadioTV dùng Ctrl+1..4 để chọn bốn mục; điều hướng Tab/Enter/Escape được giữ nhằm phục vụ người dùng bàn phím.
Không tuyên bố toàn bộ phím của hai addon đều khác nhau.

## Nguồn gốc và phần dùng chung hợp lệ

Hồ sơ dự án mô tả việc viết mới từ đặc tả, dữ liệu đài do chủ dự án cung cấp và tài liệu API.
Luồng ứng dụng hiện chia core, controller, wx UI, supervisor và worker PowerShell.
BASS/BASSHLS được đối chiếu hash với bản tải từ Un4seen; dùng cùng thư viện hoặc cùng NVDA API
không tự chứng minh mã ứng dụng được sao chép. DLL giữ giấy phép riêng.

Giấy phép mã dự án là LGPL-2.1-or-later theo quyết định đã ghi ngày 01/09/2026.
Tên thư mục radiotv-mit chỉ là tên lịch sử. Không thay giấy phép để cố tạo sự khác biệt với addon khác.

## Quyết định công bố

Ngày 04/09/2026, chủ dự án yêu cầu kiểm tra tính độc lập, kể cả phím tắt, rồi tạo kho mới và đăng mã nguồn.
Kho được chọn là https://github.com/voduykhanhmata-ctrl/radiotv, công khai.
0.1.0 được ghi là bản thử nghiệm; không mô tả rằng nghiệm thu NVDA thật hoặc review tác quyền bởi con người đã hoàn tất.
46 nguồn có token/chữ ký và một mục unsupported tiếp tục được giữ cục bộ ngoài Git.
