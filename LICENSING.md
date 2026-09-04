# Chính sách giấy phép RadioTV

## Mã do dự án viết

Mã clean-room, công cụ, kiểm thử và tài liệu do Võ Duy Khánh sở hữu được cấp
phép theo **GNU Lesser General Public License, version 2.1 or later**
(`LGPL-2.1-or-later`). Văn bản LGPL 2.1 đầy đủ nằm trong `LICENSE`; mỗi file mã
có định danh SPDX tương ứng.

Nguồn văn bản chính thức: `https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html`.

Việc đổi giấy phép chỉ áp dụng cho phần Võ Duy Khánh có quyền cấp phép. Danh mục
đài là dữ liệu do Võ Duy Khánh cung cấp và có lịch sử nguồn riêng trong
`PROVENANCE.md`. Nội dung âm thanh/truyền hình không nằm trong add-on.

## Dependency

- BASS/BASSHLS thuộc Un4seen, không thuộc LGPL. Bản hiện tại chỉ được dùng miễn
  phí trong sản phẩm phi thương mại; sản phẩm thương mại cần giấy phép phù hợp.
  Điều khoản chính thức: `https://www.un4seen.com/bass.html`.
- Windows Media Runtime là thành phần có sẵn của Windows và không được đóng gói.
- BASS_AAC không được tích hợp. Archive chính thức yêu cầu GPL nhưng không kèm mã
  nguồn tương ứng, trong khi BASS có điều khoản riêng. Đổi giấy phép RadioTV không
  tự động làm tổ hợp này hợp lệ.
- Hướng backend mở ưu tiên cho phiên bản sau là libVLC 3/4 hoặc thư viện khác có
  giấy phép LGPL tương thích. Trước khi đóng gói một thư viện mới phải lưu phiên
  bản, nguồn chính thức, hash, license, notices và cách cung cấp mã nguồn theo
  đúng nghĩa vụ của thư viện đó.
  Thông tin chính thức libVLC: `https://www.videolan.org/vlc/libvlc.html`.

## Ranh giới chức năng

Không thư viện nào được dùng để bỏ qua DRM, khóa giải mã hoặc kiểm soát truy cập.
Nguồn DASH/DRM chỉ được bật khi có backend hợp pháp và người dùng có quyền truy
cập; nếu không, chúng tiếp tục nằm ngoài gói phát hành.
