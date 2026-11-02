---
name: ultrasonic-2ring-protocol
description: >-
  Use this skill when implementing or debugging the 2-Ring Physical Presence
  Verification system: Ring 1 (2D Haversine GPS Geofencing) and Ring 2 (3D
  Near-Ultrasonic Audio 18.1kHz-20.5kHz via Web Audio API OscillatorNode and
  AnalyserNode FFT 8192 bins).
---

# 2-Ring Physical Presence Protocol: GPS Haversine & Ultrasonic Web Audio

Tài liệu kỹ thuật chuẩn cho Vòng 1 (Không gian 2D Tòa nhà) và Vòng 2 (Không gian 3D Phòng học), kế thừa từ thực nghiệm tại [`test_ultrasound/sender.html`](file:///Users/macprom2/Documents/NEU%20Agent/Code/Website%20gi%C3%BAp%20gi%E1%BA%A3ng%20vi%C3%AAn%20%C4%91i%E1%BB%83m%20danh%20sinh%20vi%C3%AAn%20nhanh%20ch%C3%B3ng/test_ultrasound/sender.html) và [`test_ultrasound/receiver.html`](file:///Users/macprom2/Documents/NEU%20Agent/Code/Website%20gi%C3%BAp%20gi%E1%BA%A3ng%20vi%C3%AAn%20%C4%91i%E1%BB%83m%20danh%20sinh%20vi%C3%AAn%20nhanh%20ch%C3%B3ng/test_ultrasound/receiver.html).

---

## 1. Vòng 1 — Định Vị Không Gian 2D Tòa Nhà (`geo_service.py` - `BR-11`, `EX-08`)

- Bán kính Trái Đất: $R = 6.371.000\text{ m}$.
- Công thức Haversine tính khoảng cách $d$ (mét) từ thiết bị sinh viên $(\varphi_{\text{sv}}, \lambda_{\text{sv}})$ tới tâm Tòa nhà $(\varphi_{\text{b}}, \lambda_{\text{b}})$:
  $$d = 2R \cdot \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \varphi}{2}\right) + \cos(\varphi_{\text{sv}})\cos(\varphi_{\text{b}})\sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)$$
- **Điều kiện hợp lệ (`BR-11`)**:
  $$d \le \text{radius\_meters} + \min(\text{max}(\text{accuracy\_sv}, 0), 100.0)$$
- Nếu vi phạm $\rightarrow$ Trả về `HTTP 400` (`EX-08`): *"Vị trí quá xa (Cách {int(d)}m). Hãy di chuyển vào khu vực giảng đường {building_name}"*.

---

## 2. Vòng 2 — Sóng Âm Cận Siêu Âm Không Gian 3D Phòng Học (`BR-09`, `BR-10`, `BR-13`, `BR-14`)

### 2.1. Tập 25 Kênh Tần Số Nhảy Tần Động (`audio_service.py` - `BR-09`)
```python
ULTRASONIC_CHANNELS_HZ = list(range(18100, 20600, 100))  # 25 kênh: 18100, 18200, ..., 20500 Hz
```
- Khi mở phiên hoặc làm mới mã QR/PIN (`refresh-qr`), hàm `pick_next_frequency(previous_freq_hz: int | None) -> int` chọn ngẫu nhiên 1 tần số trong 25 kênh sao cho **khác với `previous_freq_hz`**.
- **Hàm kiểm tra đối soát (`verify_ultrasonic_frequency` - `BR-14`, `EX-10`)**:
  - Nếu `require_audio == False` $\rightarrow$ Luôn trả về `True` (bỏ qua Vòng 2 khi phòng học hỏng loa - `BR-15`, `EX-11`).
  - Nếu `require_audio == True`:
    - Yêu cầu `detected_freq_hz` không được `None` và nằm trong dải $15.000\text{ Hz} \le \text{detected\_freq\_hz} \le 22.000\text{ Hz}$.
    - Độ lệch phải thỏa mãn:
      $$|\text{detected\_freq\_hz} - \text{audio\_freq\_hz}| \le \text{audio\_tolerance\_hz} \quad (\text{Mặc định: } \pm 50\text{ Hz})$$
    - Nếu không thỏa mãn $\rightarrow$ Trả về `HTTP 400` (`EX-10`): *"Không nhận diện được tín hiệu âm thanh phòng học (Vòng 2). Vui lòng ngồi trong phòng học và thử lại"*.

### 2.2. Chuẩn Code Bộ Phát Trên Máy Tính Giảng Viên (`useUltrasonicSender.ts` - `BR-10`)
- Dùng `OscillatorNode` với `osc.type = 'sine'`.
- **Quy tắc chống tiếng "bụp/click" trên loa hội trường**:
  - Khi bật phát: Đặt `gainNode.gain.setValueAtTime(0, ctx.currentTime)` rồi `gainNode.gain.linearRampToValueAtTime(volume, ctx.currentTime + 0.04)`.
  - Khi đổi tần số (mỗi 60s): Hạ nhẹ hoặc dùng `osc.frequency.setValueAtTime(newFreq, ctx.currentTime)` kết hợp ramp gain mượt trong $30\text{ms}-50\text{ms}$.
  - Khi dừng phát: `gainNode.gain.linearRampToValueAtTime(0, ctx.currentTime + 0.04)` rồi mới gọi `osc.stop()` sau $50\text{ms}$.

### 2.3. Chuẩn Code Bộ Thu Trên Thiết Bị Sinh Viên (`useUltrasonicReceiver.ts` - `BR-13`)
- **Bắt buộc tắt 3 bộ lọc âm thoại của smartphone** khi gọi `getUserMedia`:
  ```typescript
  const stream = await navigator.mediaDevices.getUserMedia({
    audio: {
      echoCancellation: false,
      noiseSuppression: false,
      autoGainControl: false,
      sampleRate: { ideal: 48000 }
    }
  });
  ```
- **Cấu hình `AnalyserNode`**:
  - `analyser.fftSize = 8192` ($\approx 5,86\text{ Hz/bin}$ ở $48\text{ kHz}$).
  - `analyser.smoothingTimeConstant = 0.5`.
- **Thuật toán Quét Đỉnh Tần Số**:
  - Lấy mẫu nhiều frame liên tiếp trong khoảng `1500ms` (mỗi `100ms` đọc `getByteFrequencyData(dataArray)` một lần).
  - Chỉ xét các bin $i$ có tần số $f_i = i \times \frac{\text{sampleRate}}{8192}$ nằm trong vùng **$15.000\text{ Hz} \le f_i \le 22.000\text{ Hz}$**.
  - Tìm bin có biên độ đỉnh lớn nhất vượt ngưỡng nền (`DETECTION_THRESHOLD = 35`), tính tần số đỉnh `Math.round(peakBin * binWidth)`.
  - **Ngay khi kết thúc lấy mẫu**: Gọi `stream.getTracks().forEach(t => t.stop())` và `audioCtx.close()` để tắt biểu tượng ghi âm trên điện thoại sinh viên.
