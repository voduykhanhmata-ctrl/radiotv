# Hồ sơ nguồn gốc

| Ngày | Thành phần | Nguồn | Quyền/điều khoản | Trạng thái |
|---|---|---|---|---|
| 2026-08-30 | Đặc tả chức năng | Yêu cầu của Võ Duy Khánh | Dùng cho project | Đã ghi |
| 2026-08-30 | Danh sách đài ban đầu | Võ Duy Khánh xác nhận tự thu thập | Cho phép tái sử dụng | Đã import JSON trung lập; 83 bản ghi |
| 2026-08-30 | VTV10 và nhận diện VTV6 năm 2026 | `vtv.vn` và phép thử backend | Thông tin công khai; URL chỉ được kích hoạt sau khi phát thật | Đã thêm VTV10; đã xác nhận VTV6 |
| 2026-08-30 | VOV4 khu vực | `vov.gov.vn`, `str.vov.gov.vn`, `media.kythuatvov.vn` và phép thử backend | Thông tin/điểm phát công khai | Đã thêm 4 nguồn phát được |
| 2026-08-30 | Hà Nội FM90/FM96 | `hanoionline.vn`, `tek4tv.vn` và phép thử backend | Thông tin/điểm phát công khai | Đã thêm 2 nguồn phát được |
| 2026-08-30 | Radio địa phương | Trang/điểm phát của các đài, danh mục VOH và phép thử backend | Thông tin/điểm phát công khai | Đã thêm 8 nguồn: Gia Lai, Tây Ninh, Đồng Tháp, Đà Nẵng, Đắk Nông, Huế và 2 kênh Quảng Ninh |
| 2026-08-30 | Mã project mới | Viết mới trong `radiotv-mit` | MIT | M0–M2 hoàn tất |
| 2026-08-30 | BASS 2.4.18.3 | Un4seen archive chính thức | Miễn phí phi thương mại; thương mại cần giấy phép | Đã tải mới và ghi hash |
| 2026-08-30 | BASSHLS 2.4.5 | Un4seen archive chính thức | Theo điều khoản BASS/add-on đi kèm | Đã tải mới và ghi hash |
| 2026-08-31 | Danh mục TV theo nhóm | `https://tinhlagi.pro/tv.json`, do Võ Duy Khánh cung cấp và xác nhận đã kiểm tra | Giữ mọi kênh trong nước/quốc tế tương thích; khi trùng thì ưu tiên 4K/FHD/HD; không nhập DRM/khóa vào danh sách phát | Đã nhập 570 kênh mới, ghép metadata cho 13 kênh cũ; nguồn hiện có 23 nhóm |
| 2026-08-31 | Kho nguồn chưa tương thích | Cùng danh mục TV người dùng cung cấp | Chỉ ghi tên/nhóm/URL và lý do; không ghi chỉ dẫn hoặc khóa DRM | Đã lưu riêng 30 nguồn DASH/DRM duy nhất để dùng khi có backend hợp lệ |
| 2026-08-31 | Kết quả thử bằng NVDA | Nhật ký `%TEMP%\nvda.log` của người dùng lúc 09:26:59 | Chỉ ghi tên kênh/mã lỗi, không ghi URL vào báo cáo | MMA-TV.com lỗi `stream_open_failed: 41`; không có URL cũ hoặc URL tương thích dự phòng nên đã tạm ẩn |
| 2026-08-31 | Audit Phim Sự Kiện và SCTV | Phép thử trực tiếp BASS/BASSHLS x64, âm lượng 0 | Chỉ lưu ID/tên/trạng thái/mã lỗi; URL chỉ nằm trong catalog | Phim Sự Kiện 26/43 phát; SCTV 5/20 nguồn chính phát; SCTV19 phát bằng URL dự phòng; đã tạm ẩn 31 mục lỗi còn lại |
| 2026-08-31 | Lịch phát sóng XMLTV | `https://lichphatsong.io.vn/epg.xml`, khai báo bởi danh mục TV người dùng cung cấp | Chỉ tải tạm lúc chạy, không đóng gói nội dung EPG | Đã thêm bộ tải nền và bộ đọc XMLTV |
| 2026-08-31 | Danh sách trận bóng đá | `https://tinhlagi.pro/s.m3u`, từ `https://bit.ly/tinhlagibongda` do Võ Duy Khánh cung cấp | Chỉ nhập HLS trực tiếp; loại mục giới thiệu, FLV và biến thể trùng; không ghi DRM/khóa | Đã cập nhật 168 trận/nguồn HLS duy nhất vào tab Bóng đá; trạng thái phát từng trận vẫn cần backend xác minh |
| 2026-09-01 | BASS bản chính thức mới nhất | `https://www.un4seen.com/stuff/bass.zip` | Điều khoản BASS của Un4seen; phi thương mại miễn phí, thương mại cần giấy phép | Đã thay BASS x64/x86 bằng 2.4.18.23; sửa lỗi mở một số luồng SCTV |
| 2026-09-01 | Làm mới SCTV và nguồn từng bị ẩn | Danh mục TV do Võ Duy Khánh cung cấp | Giữ nguồn HLS/HTTP(S), chỉ giữ metadata User-Agent an toàn; không lưu DRM/khóa | 21 SCTV tương thích được bật và xác nhận phát; 43 Phim Sự Kiện được bật và xác nhận phát; ba SCTV DASH/DRM vẫn ở kho không đóng gói |
| 2026-09-01 | Đường phát dự phòng | Windows Media Runtime có sẵn trong Windows | Thành phần hệ điều hành, không phân phối kèm add-on | Dùng một lần khi BASS không mở hoặc dừng trước `playing`; xác nhận được hai nguồn sự kiện còn lỗi |
| 2026-09-01 | Audit playback sau khôi phục | Worker thật, âm lượng 0 | Báo cáo không ghi URL luồng | x64: SCTV 21/21, Phim Sự Kiện 43/43; x86: SCTV3 bằng BASS và một nguồn bằng Windows Media Runtime đều phát |
| 2026-09-01 | Đổi giấy phép mã project | Quyết định của Võ Duy Khánh, chủ sở hữu mã clean-room | `LGPL-2.1-or-later`; dependency vẫn giữ điều khoản riêng | Đã thay LICENSE, SPDX, manifest, Help và kiểm thử; chuẩn bị dev6 |
| 2026-09-01 | Khôi phục radio cũ | Endpoint đang được chính trang VOV/VOVWorld và VOH công bố, cùng phép thử backend | URL phát công khai; không đóng gói nội dung | VOV Giao thông Hà Nội và sáu nguồn VOV/VOH được xác nhận phát; XONE/VSBet tiếp tục tắt |

## Hash dependency M3

- `bass24.zip`: `3A03EC9A33D0F4F9D167660DA51C8BB1432E8977496995455AB137277D69636E`
- `basshls24.zip`: `7531BC714DDE5A996D1C106B6F7AD08103611DE05BD38423D46A01711AF7E574`
- x64 `bass.dll`: `FEBB2CF1882D554C3A958280777DA0B69F07DE6E262DF271DE11C56E4A54AFD4`
- x64 `basshls.dll`: `9E970D27BD2048514F38A8C6A87009F2BD8AAA6D4CB29A3CA7ABF2035CFA3C6B`
- x86 `bass.dll`: `CE5E97630CF4E1EF12A9AFAD785683414B7504EFC443766333360AD2ED142EBA`
- x86 `basshls.dll`: `509AC59D77E094F6E70A1202A050534B1D128D0B822AF0BC7600200EE6534530`

## Hash dependency cập nhật 2026-09-01

- `bass-latest-build.zip` 2.4.18.23: `FBDB33BC3FE1DC9056C3A8AA2AB6D99268DCDF62476C56E7D8F4B5B299EE9515`
- x64 `bass.dll` 2.4.18.23: `7F4CBC4BE64B996811F3A7E46207F75D7A1C8991830C58AF8E8D3F860AF807C6`
- x86 `bass.dll` 2.4.18.23: `28D9BCF8265142979E5DBA0AE4BCE38ED70BC84173B64C54A71B8684273FB7E6`
- x64 `basshls.dll` 2.4.5: `9E970D27BD2048514F38A8C6A87009F2BD8AAA6D4CB29A3CA7ABF2035CFA3C6B`
- x86 `basshls.dll` 2.4.5: `509AC59D77E094F6E70A1202A050534B1D128D0B822AF0BC7600200EE6534530`

BASS_AAC đã được xem xét nhưng không được tích hợp vì nghĩa vụ GPL/phân phối mã
nguồn của archive thử nghiệm. Không có file BASS_AAC trong project hoặc gói.

## Gói thử 0.1.0-dev6

- File: `dist/RadioTV-0.1.0-dev6.nvda-addon`
- Số file: 30
- Kích thước: 457.912 byte
- SHA-256: `E84538A611D82BA8DA58A3B2EF246199C11A21A7F16591EB8A20AF9AEB690D2F`
- CRC: đạt; dựng lại hai lần cho cùng mã băm.
- `LICENSE` LGPL 2.1 chính thức SHA-256:
  `20E50FE7AAE3E56378EBF0417D9DE904F55A0E61E4DF315333E632A4D3555D95`.

Không file mã nguồn nào từ FreeRadio hoặc RadioTV cũ được đưa vào project này.

## Rà soát chuẩn bị 0.1.0 — 2026-09-04

- Giữ quyết định LGPL-2.1-or-later ngày 2026-09-01; đồng bộ AGENTS.md vốn còn ghi MIT.
- Kiểm tra toàn bộ mã Python/PowerShell do dự án sở hữu, công cụ, kiểm thử, Help,
  dữ liệu và metadata. DLL chỉ kiểm tra hash/nguồn/điều khoản; không có mã nội bộ Un4seen để audit.
- Bốn DLL khớp chính xác bảng hash cập nhật 2026-09-01; không lấy thư viện từ dự án cũ.
- Dùng CPython **3.11.9 portable** chính thức chỉ để kiểm thử x64/x86, không phân phối kèm addon:
  nguồn `https://www.python.org/downloads/release/python-3119/`.
  SHA-256 archive x64: `009D6BF7E3B2DDCA3D784FA09F90FE54336D5B60F0E0F305C37F400BF83CFD3B`;
  x86: `DAF24DE7FB3B173E94E56A201D3F38DFEDEBBDC7ED1925F7AEB8ED588E2B4189`.
  Đây là môi trường tái hiện kiểm thử, không phải khuyến nghị phiên bản Python mới nhất.
- Tài liệu đối chiếu: API BASS_ChannelIsActive tại `https://www.un4seen.com/doc/bass/BASS_ChannelIsActive.html`,
  điều khoản BASS tại `https://www.un4seen.com/bass.html`, API global plugin NVDA tại
  `https://github.com/nvaccess/nvda/blob/master/source/globalPluginHandler.py`.
- Snapshot công khai bỏ 46 mục có tham số token/chữ ký và một mục trong kho chưa hỗ trợ.
  Dữ liệu đầy đủ được lưu cục bộ trước khi thay thế, không đưa vào Git hoặc archive phát hành.
  Catalog công khai: 786 mục, 784 bật; 595 TV, 30 radio, 161 thể thao. Không coi mọi mục là phát được.
- Smoke thật, âm lượng 0: VOV1 HLS và RFI Việt MP3 đều báo `playing` trên x64/x86.
  Chỉ hai nguồn đại diện được thử lần này; không tuyên bố tái xác nhận toàn bộ 786 nguồn.
- So sánh chỉ qua chương trình tự động: 16 file Python mới, 12 file của snapshot FreeRadio
  trong Git index cục bộ và 11 file RadioTV cũ. Không lỗi parse, không file trùng byte,
  không cửa sổ 80 token trùng trong các hàm đủ dài, kể cả phép chuẩn hóa tên/literal.
  Không xuất code, symbol, tên file cũ hoặc đoạn khớp vào ngữ cảnh triển khai.
  Đo lường bỏ qua import, dữ liệu, hằng module, hàm ngắn và DLL; không chứng minh quyền tác giả tuyệt đối.
- Các tuyên bố lịch sử ở trên là hồ sơ của dự án. Lượt này chỉ xác minh hiện trạng trong
  phạm vi ghi rõ; review provenance độc lập và nghiệm thu NVDA thật của 0.1.0 còn chờ.


## Cập nhật công bố mã nguồn — 2026-09-04

Chủ dự án đã yêu cầu đối chiếu tính độc lập/phím tắt và tạo kho GitHub mới để đăng mã nguồn.
Kho đích: https://github.com/voduykhanhmata-ctrl/radiotv. Phiên bản 0.1.0 được ghi là bản thử nghiệm.
Năm phím toàn cục không trùng snapshot FreeRadio; các phím trong cửa sổ dùng quy ước quen thuộc.
Xem reports/INDEPENDENCE_AND_SHORTCUTS_2026-09-04.md để biết phương pháp và giới hạn.
Chưa xác nhận nghiệm thu NVDA thật hoặc review của người độc lập; không đổi trạng thái các bước đó thành hoàn tất.
