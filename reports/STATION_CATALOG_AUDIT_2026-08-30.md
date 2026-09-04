# Kiểm tra danh mục đài Việt Nam — 30/08/2026

## Kết quả áp dụng

- Danh mục được chia thành ba khối cố định: TV, radio, thể thao.
- TV quốc gia đứng trước; tiếp theo là các kênh chính luận, Hà Nội, HTV và đài địa phương/cáp theo tên.
- Radio VOV đứng trước; tiếp theo là Hà Nội, VOH và radio địa phương theo tên.
- Thêm 15 đài/nguồn mới chỉ sau khi backend BASS/BASSHLS báo trạng thái `playing` trên cả x64 và x86.
- `vn-vsbet` bị tắt vì backend báo `stream_open_failed: 41`.
- Không build và không phát hành trong lượt cập nhật dữ liệu này.

## Nguồn mới phát thành công

| ID | Tên | Kết quả |
|---|---|---|
| `vn-vtv10` | VTV10 - Tây Nam Bộ | Phát thành công |
| `vn-vov4-taybac` | VOV4 - Tây Bắc | Phát thành công |
| `vn-vov4-taynguyen` | VOV4 - Tây Nguyên | Phát thành công |
| `vn-vov4-dbscl` | VOV4 - Đồng bằng sông Cửu Long | Phát thành công |
| `vn-vov4-hcmc` | VOV4 - TP.HCM | Phát thành công |
| `vn-hanoi-fm90` | Hà Nội FM90 - Tin tức và Giao thông | Phát thành công |
| `vn-hanoi-fm96` | Hà Nội FM96 | Phát thành công |
| `vn-gialai-radio` | Gia Lai Radio | Phát thành công |
| `vn-tayninh-radio` | Tây Ninh FM96.9 / 103.1 | Phát thành công |
| `vn-dongthap-radio` | Đồng Tháp FM96.2 / 98.4 | Phát thành công |
| `vn-danang-radio` | Đà Nẵng FM98.5 | Phát thành công |
| `vn-daknong-radio` | Đắk Nông Radio | Phát thành công |
| `vn-hue-radio` | Huế FM93.0 | Phát thành công |
| `vn-quangninh-qnr1` | Quảng Ninh QNR1 - FM97.8 | Phát thành công |
| `vn-quangninh-qnr2` | Quảng Ninh QNR2 - FM94.7 | Phát thành công |

`vn-vtv6-iptv` cũng được kiểm tra lại và phát thành công. VTV xác nhận VTV6 đã trở lại với định hướng kênh thể thao trong năm 2026, vì vậy tên hiện tại được giữ lại.

## Ứng viên chưa thêm vì không phát được

- VOV6.
- VOV4 Đông Bắc.
- VOV Giao thông Duyên Hải.
- Hải Phòng FM93.7 và FM102.2.
- Đà Nẵng FM98.5.
- Cần Thơ FM97.3.
- Bắc Ninh FM92.1.
- Hưng Yên FM92.7.
- Hà Tĩnh FM93.6.
- An Giang FM99.4.

Các mục này chỉ là ứng viên nguồn; không được đưa vào danh mục hoạt động để tránh tạo đài bấm vào nhưng không nghe được.

## Nguồn cũ được rà lại

- Phát trên x64 và x86: VOV2, VOV3, VOV5, VOV Giao thông TP.HCM, VOV Mekong (đã thay URL) và Zing Bolero.
- Tạm ẩn vì không phát: VOV Giao thông Hà Nội, VOV English 24/7, VOV5 World, VOH FM99.9, VOH FM95.6, VOH FM87.7, VOH AM610 và XONE FM.
- Trang VOH vẫn công bố các kênh VOH nhưng URL hiện tại trả về định dạng backend không mở được (`stream_open_failed: 41`), vì vậy chưa được bật lại.

## Trang xác minh nhận diện

- VTV10: <https://vtv.vn/vtv-can-tho.html>
- VTV6 thể thao: <https://vtv.vn/kenh-the-thao-vtv6.html>
- Hệ thống kênh VOV: <https://vov.gov.vn/chuc-nang-nhiem-vu-dtnew-128346>
- Hà Nội FM90/FM96: <https://hanoionline.vn/lich-phat-song/FM90.htm>
- Tây Ninh FM96.9/FM103.1: <https://baotayninh.vn/thong-bao-ve-viec-phat-song-fm-tren-2-tan-so-96-9-mhz-va-103-1-mhz-137661.html>

## Phạm vi chưa hoàn tất

“Đủ các đài Việt Nam” được hiểu là đủ các kênh công khai mà addon có thể mở trực tiếp. Danh mục vẫn cần một lượt rà soát toàn bộ các nguồn cũ và tiếp tục tìm nguồn thay thế cho tỉnh/thành còn thiếu. HTTP 200 hoặc có tệp playlist không được xem là thành công; chỉ trạng thái `playing` của backend mới được chấp nhận.
