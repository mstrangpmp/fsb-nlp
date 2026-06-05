# Báo Cáo Phân Tích Lỗi GPT-4o-mini (Vai trò: Kỹ sư Prompting)

**Người thực hiện**: Đỗ Trọng Minh Quân

**Mục tiêu**: Phân tích định tính 3 lỗi của mô hình GPT trong việc tự động tạo bài quảng cáo Bất động sản dựa trên dữ liệu Test.

---

## Lỗi 1: Không linh hoạt làm tròn số liệu (Quá máy móc)
- **Mẫu phát hiện**: Mẫu ID 0 (Điện Biên Phủ, Quận 10).
- **Kết quả dự đoán của GPT**: Tiêu đề ghi `38.7m2 (4.06x7.5)`.
- **Mô tả chuẩn (Groundtruth)**: Tiêu đề ghi `39m2 (4.1x7.5)`.
- **Phân tích định tính**: GPT có xu hướng "bê nguyên xi" các con số lẻ từ mô tả thô vào tiêu đề. Điều này làm tiêu đề bị rối mắt. Một chuyên viên môi giới (như trong groundtruth) sẽ chủ động làm tròn số (4.06 -> 4.1, 38.7 -> 39) để thông số đẹp hơn, gọn gàng hơn và thu hút khách hàng hơn. GPT hiện tại chưa có được sự tinh tế marketing này.

## Lỗi 2: Văn phong rập khuôn, thiếu điểm nhấn (Generic Phrases)
- **Mẫu phát hiện**: Mẫu ID 1 (Cao Thắng, Quận 3) và ID 2 (CMT8, Quận 10).
- **Kết quả dự đoán của GPT**: Liên tục xài các slogan mẫu chung chung như *"CƠ HỘI ĐẦU TƯ TẠI QUẬN 3..."* hay *"CĂN NHÀ ĐẸP TẠI QUẬN 10..."*.
- **Mô tả chuẩn (Groundtruth)**: Slogan được giật tít bằng các địa danh nổi tiếng: *"TRUNG TÂM QUẬN 3 NÚT GIAO CAO THẮNG NGUYỄN THIỆN THUẬT..."* hoặc *"LIỀN KỀ CÔNG VIÊN LÊ THỊ RIÊNG..."*.
- **Phân tích định tính**: AI thiếu khả năng nhận diện những lợi thế về mặt "landmark" (địa danh) xung quanh ngôi nhà. Nó chỉ tóm tắt lại những gì có sẵn thay vì chủ động bốc tách một tên đường lớn hoặc tiện ích nổi bật nhất đưa lên Slogan để làm "mồi câu" (hook) người đọc.

## Lỗi 3: Không hiểu từ lóng / thuật ngữ chuyên ngành (Lack of Domain Knowledge)
- **Mẫu phát hiện**: Mẫu ID 4 (Lê Văn Sỹ, Quận 3).
- **Kết quả dự đoán của GPT**: Ghi nhận diện tích là `35m2`.
- **Mô tả chuẩn (Groundtruth)**: Ghi nhận diện tích là `40m2`.
- **Phân tích định tính**: Trong dữ liệu thô có chuỗi `35/40`. Trong ngành môi giới, đây là từ lóng ám chỉ "Diện tích công nhận là 35, diện tích sử dụng là 40". GPT hoàn toàn không hiểu ngữ cảnh chuyên ngành này, nên đã ưu tiên lấy con số đầu tiên. Trong khi đó, người viết quảng cáo thật sẽ dùng con số 40m2 để làm nổi bật sự rộng rãi của căn nhà.

---

### Đề xuất hướng cải thiện (Prompt Tuning)
Để khắc phục 3 lỗi này trong các lần gọi API tới, ta cần sửa lại `system_prompt`:
1. Cấp quyền cho AI làm tròn một số thập phân (VD: `4.06 -> 4.1`).
2. Yêu cầu AI bắt buộc phải trích xuất một tên đường, trường học hoặc chợ lớn đưa vào dòng in hoa đầu bài.
3. Giải thích thêm quy tắc đọc hiểu từ lóng (VD: `"A/B" nghĩa là xài số B`).



## Đánh Giá Định Lượng (Quantitative Metrics)
| Mô Hình Chạy Thử | ROUGE-L (TB) | BERTScore (TB) | Specs Pres. (TB) | Độ Trễ (Latency) | Chi Phí (Cost/1k) | Trạng Thái |
|---|---|---|---|---|---|---|
| GPT-4o mini API | 46.78% | 80.79% | 46.08% | 7.40 giây | ~13,983đ | Hoàn thành |
