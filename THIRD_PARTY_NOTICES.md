# Thành phần bên thứ ba

## BASS 2.4.18.23 và BASSHLS 2.4.5

- Nhà cung cấp: Un4seen Developments.
- Nguồn BASS đang dùng: `https://www.un4seen.com/stuff/bass.zip`.
- Nguồn BASSHLS: `https://www.un4seen.com/files/basshls24.zip`.
- Mục đích: phát luồng MP3/HTTP(S) và HLS trong tiến trình tách khỏi NVDA.
- Điều khoản: miễn phí cho cá nhân/tổ chức phi thương mại khi sản phẩm không tạo
  doanh thu; sử dụng thương mại cần giấy phép BASS phù hợp.
- Mã RadioTV do dự án viết theo `LGPL-2.1-or-later`; các DLL BASS không thuộc
  LGPL và không
  được phép bán lại hoặc cấp phép con độc lập.
- Văn bản gốc tải kèm được lưu tại `third_party/BASS/BASS.txt` và
  `third_party/BASS/BASSHLS.txt`.

BASS_AAC không được đưa vào mã, runtime hoặc gói phát hành. Archive chính thức
chỉ kèm DLL và yêu cầu tuân theo GPL nhưng không kèm mã nguồn tương ứng; việc đổi
giấy phép RadioTV không xóa nghĩa vụ đó hoặc giới hạn riêng của BASS. RadioTV dùng Windows Media Runtime
có sẵn trong hệ điều hành cho các luồng BASS không mở được. Thành phần Windows này
không được phân phối kèm add-on.

Bản dev 0.1 chỉ dành cho kiểm tra phi thương mại. Trước phát hành chính thức phải
xác nhận chủ dự án vẫn đáp ứng điều kiện phi thương mại hoặc thay backend/mua giấy
phép phù hợp.

Bản 0.1.0 là ứng viên chuẩn bị công bố; các giới hạn BASS áp dụng cả khi mã RadioTV
được công khai. LGPL của RadioTV không cấp quyền thương mại hoặc quyền cấp phép lại DLL của Un4seen.

## Danh mục TV và lịch phát sóng do người dùng cung cấp

- Danh mục: `https://tinhlagi.pro/tv.json` (nội dung thực tế là M3U).
- Lịch XMLTV: `https://lichphatsong.io.vn/epg.xml`.
- RadioTV giữ các kênh trong nước và quốc tế có luồng HTTP(S) trực tiếp. Khi một
  kênh có nhiều biến thể, bộ nhập ưu tiên nhãn 4K/FHD/HD rồi loại bản trùng thấp hơn.
- Chỉ dẫn User-Agent của từng nguồn được kiểm tra độ dài/ký tự và lưu dưới dạng
  metadata tối thiểu; header tùy ý, cookie, khóa hoặc chỉ dẫn DRM không được giữ.
- Bộ nhập cố ý loại MPEG-DASH, chỉ dẫn Kodi, DRM và khóa giải mã. Tên/nhóm/URL
  của nguồn không tương thích chỉ nằm trong hồ sơ phát triển không đóng gói.
- Nội dung truyền hình không được đóng gói hay phân phối bởi add-on. Quyền xem,
  điều kiện truy cập và độ ổn định thuộc nhà cung cấp tương ứng.

Snapshot ngày 2026-09-04 đã loại các URL có tham số token/chữ ký khỏi dữ liệu công khai.
Việc một URL không chứa tham số nhạy cảm không tự chứng minh quyền phân phối nội dung hoặc độ ổn định.

## Danh sách trận bóng đá do người dùng cung cấp

- Danh mục: `https://tinhlagi.pro/s.m3u`, được mở từ link rút gọn do người dùng
  cung cấp.
- RadioTV chỉ nhập URL HLS trực tiếp và loại các mục FLV, hình giới thiệu cùng
  biến thể trùng. Add-on không đóng gói nội dung thể thao.
- Lịch trận và URL có thể thay đổi theo thời gian. Quyền xem, điều kiện truy cập
  và độ ổn định thuộc nhà cung cấp tương ứng.
