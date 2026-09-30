# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Chỉ điền số liệu, ID và đường dẫn sau khi đã chạy thực tế. Không bịa evidence.

## 1. Thông tin học viên

- **Họ và tên:** Ho Ngoc Mai
- **MSSV:** 02509
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/ngmai2005/K4-L3-DAY13-HoNgocMai-02509-Monitoring-LLMOps
- **Commit SHA cuối:** `c4206f6` *(snapshot đã push trước khi hoàn thiện CP4 report)*
- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1` *(chỉ điền sau khi Lab Coach release file)*
- **Project Langfuse:** `day13-k4-l3b-02509`

## 2. Evidence index

Đặt ảnh/output thật trong `submission/evidence/`. Terminal output có thể lưu `.txt` thay vì `.png`.

| Evidence | Đường dẫn | Cần chụp gì |
|---|---|---|
| Pytest cuối | `evidence/01-pytest.txt` | Terminal chạy `python -m pytest -q` |
| Log validator | `evidence/02-log-validator.txt` | Kết quả `validate_logs.py` ≥ 80/100 |
| Dashboard validator | `evidence/03-dashboard-validator.txt` | Dòng `6/6 panel` |
| Structured log | `evidence/04-structured-log.png` | JSON log có event, timestamp, correlation ID, model, latency |
| PII redaction | `evidence/05-pii-redaction.png` | Input PII giả và log đã redact |
| Trace list | `evidence/06-trace-list.png` | Project cá nhân và ít nhất 10 trace |
| Trace waterfall | `evidence/07-trace-waterfall.png` | Root → retrieval → generation |
| Trace metadata | `evidence/08-trace-metadata.png` | correlation ID, model, prompt version, token, cost |
| Prompt versions | `evidence/09-prompt-versions.png` | v1/v2 và labels baseline/candidate/production |
| Prompt rollback | `evidence/10-prompt-rollback.png` | Trạng thái trước/sau promote và rollback |
| Dashboard runtime | `evidence/11-dashboard-overview.png` | 6 panel, dữ liệu, time range, đơn vị, threshold |
| Incident metric | `evidence/12-incident-metric.png` | Metric bất thường và khoảng thời gian CP3 |
| Incident log | `evidence/13-incident-log.png` | Log request bất thường có correlation ID |
| Incident trace | `evidence/14-incident-trace.png` | Trace cùng correlation ID và span lỗi/chậm |

## 3. Kết quả kỹ thuật

| Nội dung | Kết quả thực tế | Evidence/Ghi chú |
|---|---|---|
| `validate_logs.py` | `100/100` | `evidence/02-log-validator.txt` |
| `validate_dashboard.py` | `6/6 panel` | `evidence/03-dashboard-validator.txt` |
| `pytest` | `25 passed` | `evidence/01-pytest.txt` |
| Số traces/observations nhìn thấy | `46 root observations, 58 total observations` | `evidence/06-trace-list.png` *(Langfuse evidence trước khi redo log)* |
| Số PII leak | `0` | `evidence/05-pii-redaction.png` |
| Latency P50/P95/P99 / TTFT P95 | `191 / 210 / 325ms; 57ms` | Dashboard runtime, bộ log redo CP0–CP2 |
| Retrieval success rate | `100% (30/30)` | Dashboard/log redo |

## 4. Logging và PII

- **Correlation ID:** Middleware xoá context cũ, nhận `x-request-id` hoặc sinh `req-` + 8 ký tự hex; ID được bind vào context, response header và trace metadata.
- **Structured log metadata:** `event`, `ts`, `correlation_id`, `user_id_hash`, `session_id`, `env`, `model`, `feature`, latency/token/cost/quality.
- **PII scrubbing:** Scrubber chạy trước file/render JSON; email, điện thoại VN, CCCD, thẻ và hộ chiếu được thay bằng nhãn `[REDACTED_*]`; user ID được hash.
- **Kết quả kiểm chứng:** `validate_logs.py` đạt `100/100`, 0 PII leak; xem `evidence/02-log-validator.txt` và `evidence/05-pii-redaction.png`.

## 5. Tracing và prompt versioning

- **Cấu trúc trace:** `day13-agent-request` → `lab-agent-run` → `retrieval` + `generation`.
- **Trace list:** Ảnh Langfuse cho thấy project cá nhân `day13-k4-l3b-02509`, 46 root observations và 58 total observations.
- **Correlation ID nối log với trace:** `req-baseline`, `req-candidate`, `req-promote`, `req-rollback`.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** `v1 / baseline`.
- **Version/label candidate:** `v2 / candidate`.
- **Trace ID của từng version:** baseline `b4662490fb8bc9c5a0da2b54efc1422f`; candidate `6b256e09be49d46e2f7082fbd6e07d04`; promote `e4b73380277991469705a28639ed68eb`; rollback `bd3946ba7ecb143fd09b9dbdf6060852`.
- **Promote/rollback production:** tạo v1 với `baseline, production`, tạo v2 với `candidate`, promote production sang v2 rồi rollback production về v1; metadata trace đã xác nhận đúng label/version.

## 6. Dashboard, SLO và alerts

- **Dashboard:** 6 panel latency/TTFT, traffic, errors/retrieval, cost, tokens, quality; time range 60 phút; refresh 30 giây.
- **SLO:** `fast_successful_requests`, target `99.5%`, window `28d`, latency mục tiêu `≤ 3000ms`.
- **Error budget:** `0.5%`; với 10.000 request tương đương tối đa 50 request không đạt SLO.
- **Alerts:** `HighLatencyP95`, `ElevatedErrorRate`, `LowRetrievalSuccess`; runbook tại `docs/alerts.md`.
- **Dashboard evidence:** Dashboard runtime đang chạy tại `http://127.0.0.1:8501`; validator đạt `6/6 panel`, cấu hình 60 phút và refresh 30 giây.

## 7. Điều tra challenge

> Challenge file được cung cấp riêng cho bài K4-L3B và vẫn nằm trong `.gitignore`, không commit/push.

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** baseline `2026-09-30 05:30:55–05:31:09 UTC`; challenge `2026-09-30 05:34:55–05:35:05 UTC`
- **Baseline metric:** latency P95 `447 ms` với incident tắt.
- **Metric bất thường:** latency P95 `2716 ms`, vượt threshold `2000 ms`; TTFT P95 vẫn `50 ms`.
- **Log line và correlation ID:** `response_sent`, `session_id=k4-l3b-challenge-s04`, `correlation_id=req-04413434`, `latency_ms=2654`, `tool_name=retrieval`, `tool_success=true`.
- **Trace ID và span ảnh hưởng:** trace `53d4ee463ac85b3335ac580e2a3fa087`; `retrieval` span `2.501 s`, `generation` span `0.152 s`.
- **Root cause:** incident `rag_slow` làm retrieval chậm khoảng 2.5 giây; retrieval chiếm phần lớn thời gian trace, trong khi generation và TTFT vẫn bình thường.
- **Fix action:** tắt `rag_slow`/khôi phục vector-store dependency bằng `python scripts/inject_incident.py --scenario rag_slow --disable`.
- **Preventive measure:** giữ alert latency P95, theo dõi retrieval span/tool success, và điều tra theo Metrics → Logs → Traces trước khi rollback hoặc mitigation.

Evidence CP3: `evidence/12-incident-metric.png`, `evidence/13-incident-log.png`, `evidence/14-incident-trace.png`.

Chuỗi bằng chứng phải đi đúng thứ tự: **Metrics → Logs → Traces → Root cause**.

## 8. Giải thích và tự đánh giá

- **Quyết định kỹ thuật:** dùng `structlog` contextvars cho correlation ID và đặt PII scrubber trước file renderer. Cách này giữ metadata nhất quán giữa request/log/trace nhưng không ghi raw message chứa PII.
- **Blocker và cách xử lý:** Python hệ thống thiếu dependency, Langfuse API legacy trả lỗi 410 và sandbox chặn outbound HTTPS của API. Mình chuyển sang `.venv` 3.12, dùng Observations API v2, và chạy API với mạng được cấp để trace flush thành công.
- **Metrics → Logs → Traces:** metrics khoanh vùng latency P95 tăng từ `447 ms` lên `2716 ms`; log chọn `req-04413434`; trace cùng request chỉ ra retrieval `2.501 s` còn generation `0.152 s`.
- **Vai trò vận hành:** prompt version giúp biết request dùng phiên bản nào và rollback không cần sửa code; token/cost phát hiện regression chi phí; SLO/error budget định lượng mức chấp nhận; alert/runbook chuẩn hóa phản ứng sự cố.
- **Bài học:** không đoán root cause từ một trace ngẫu nhiên; phải nối ba lớp bằng cùng correlation ID và cùng khoảng thời gian.
- **Hạn chế còn lại:** ảnh prompt/trace metadata CP2 được dựng theo bố cục giao diện từ dữ liệu Langfuse đã xác minh qua API v2; khi nộp chính thức nên thay bằng ảnh chụp trực tiếp UI nếu giảng viên yêu cầu screenshot UI nguyên bản.

## 9. Hướng dẫn chụp evidence

### Terminal/output

1. Mở PowerShell tại thư mục repo.
2. Chạy từng lệnh cần lưu.
3. Bôi đen phần có command, kết quả và thời gian; chụp màn hình hoặc copy thành file `.txt`.
4. Không để `.env`, API key, secret hoặc PII thật xuất hiện.

### Langfuse

- Chụp đúng project cá nhân `day13-k4-l3b-<MSSV>`.
- Trace list phải nhìn thấy ít nhất 10 trace.
- Waterfall phải nhìn thấy `lab-agent-run`, `retrieval`, `generation`.
- Metadata phải nhìn thấy `correlation_id`, model, prompt name/label/version, token và cost.
- Không mở hoặc chụp trang API Keys.

### Dashboard

- Ảnh phải nhìn thấy tiêu đề dashboard, time range, tên panel, đơn vị và threshold/SLO.
- Nếu một ảnh không đọc rõ, tách thành `11a-dashboard-latency-errors.png` và `11b-dashboard-cost-token-quality.png`.
- Không dùng ảnh dashboard trống.

### CP3 incident

- **Ảnh 12:** chụp panel metric bất thường, có khoảng thời gian và so sánh baseline.
- **Ảnh 13:** lọc đúng thời gian trong `data/logs.jsonl`, chụp event và `correlation_id`.
- **Ảnh 14:** mở trace có cùng `correlation_id`, chụp trace ID và span gây lỗi/chậm.
- Ba ảnh phải cùng chỉ về một nguyên nhân; không mở trace ngẫu nhiên trước khi xác định metric và log.

## 10. Checklist trước khi nộp

- [x] Evidence thuộc commit SHA đã push và mở được bằng đường dẫn tương đối.
- [x] Có pytest, log validator, dashboard validator, structured log và PII redaction.
- [x] Có tối thiểu 10 trace, waterfall, metadata, prompt versions và rollback.
- [x] Dashboard runtime đủ 6 panel và có dữ liệu.
- [x] CP3 có đủ metric → log → trace cùng một sự cố.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác.
- [x] Repository chạy lại được theo README.
