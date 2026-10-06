# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Phạm Quang Đạt | 2A202602704 | Cá nhân |

- Mô hình: `LAB_MODEL=openai:gpt-4o-mini`; `LAB_TEMPERATURE=0`; `recursion_limit=60`.
- Deep Agents `0.7.21`; container Linux trên Docker Desktop/WSL2 (`Linux 6.18.33.2-microsoft-standard-WSL2`, Python 3.12).
- Số lần chạy tác vụ: 28 lượt trong toàn bộ thí nghiệm, gồm 19 lượt ở Phần 4 (12 lượt chính thức ban đầu và 7 lượt retry đúng một lần theo GUIDE); ngoài ra curator gọi mô hình một lần. Không đặt ngân sách cứng.
- Commit của tag `freeze`: `7428d08a1f285e80ebb6c7c4125f4adea54536db` (`freeze skills`, 2026-10-06T12:55:07+07:00).

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

- H1 (subagents so với baseline): Dự đoán `baseline` đạt điểm đánh giá trung bình bằng hoặc cao hơn `subagents`. Trong ba tác vụ học, `subagent_calls=0` ở cả ba nên chưa có cơ chế đa tác tử thực sự, trong khi token trung bình của cấu hình `subagents` cao hơn 119,6% và điểm chỉ tăng từ 0,175 lên 0,183. Hướng dẫn của lab cũng dẫn nghiên cứu Anthropic cho thấy đa tác tử thường có chi phí token lớn, nên không kỳ vọng lợi ích khi không có giao việc thực tế.
- H2 (skills-auto so với baseline): Dự đoán `baseline` đạt điểm đánh giá trung bình cao hơn `skills-auto`. Ở Phần 3.4, điểm học trung bình của `skills-auto` là 0,0417 so với 0,175 của baseline; hai run có trace đều không đọc skill, còn hai skill được giữ chỉ liên quan type annotation, changelog và regression test nên không bao phủ tác vụ dữ liệu/log. Căn cứ bổ sung từ hướng dẫn: SkillsBench ghi nhận skill do mô hình tự sinh trung bình không có lợi, và SkillEvolBench cảnh báo lợi ích trên tập học thường không chuyển sang tác vụ mới.
- H3 (tác vụ học so với tác vụ đánh giá): Dự đoán điểm đánh giá không cao hơn điểm học ở cả ba điều kiện, và chênh lệch giảm rõ nhất ở `skills-auto`. Tác vụ đánh giá có thêm quy ước mới, trong khi phân loại baseline cho thấy 6/21 lỗi thuộc nhóm E và các skill hiện tại không bao phủ quy ước dữ liệu/log. Nếu skill chỉ phản ánh feedback của tập học, quy ước mới là phép thử trực tiếp cho quá khớp như cảnh báo của SkillEvolBench.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Tác tử mặc định có những công cụ nào? Công cụ nào cho phép chạy lệnh?

Tác tử mặc định có 9 công cụ:

`ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`, `execute`, `task`.

Trong đó, `execute` là công cụ cho phép chạy lệnh shell. Công cụ này thực thi một shell command trong sandbox và trả về stdout, stderr cùng exit code.

2. Mô tả của công cụ task nói gì về subagent general-purpose? Subagent đó nhìn thấy ngữ cảnh nào của tác tử chính?

Subagent general-purpose được mô tả là một agent đa dụng, có khả năng nghiên cứu các câu hỏi phức tạp, tìm kiếm file/nội dung và thực hiện các task nhiều bước. Subagent này có quyền truy cập vào tất cả các công cụ giống tác tử chính.

Tuy nhiên, mỗi lần gọi general-purpose là stateless theo mặc định: subagent chỉ nhìn thấy prompt được truyền trực tiếp cho nó, không tự động nhìn thấy toàn bộ conversation/context của tác tử chính. Vì vậy cần cung cấp đầy đủ thông tin cần thiết trong prompt.

3. System prompt mặc định của Deep Agents rỗng. Trích một câu hướng dẫn hành vi từ mô tả của task và một câu từ mô tả của execute.

Từ mô tả của `task`: “Launch multiple agents concurrently when their tasks are independent, using a single message with multiple tool calls.”

Câu này hướng dẫn tác tử chạy nhiều subagent song song khi các task độc lập.

Từ mô tả của `execute`: “You MUST avoid using search commands like find and grep. Instead use the grep, glob tools to search.”

Câu này hướng dẫn tác tử không sử dụng các lệnh tìm kiếm find và grep thông qua shell, mà phải sử dụng các tool grep và glob tương ứng.

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| `code-learn` | `parse_price_all_formats` | A. Bỏ qua đặc tả | `detail`: `wrong for: ['(12.00)']`. Vết cho thấy tác tử đã đọc docstring có trường hợp số âm kiểu kế toán nhưng chỉ thêm xử lý dấu phẩy. |
| `code-learn` | `csv_quoting_follows_docstring` | A. Bỏ qua đặc tả | `detail`: `to_csv_row returned 'Desk, large "oak",10.00,2'`. Tác tử đọc quy tắc RFC 4180 trong docstring nhưng không sửa `export.py`. |
| `code-learn` | `rule_type_hints` | E. Vi phạm quy ước tổ chức | `detail`: `RULE: every public function ... has type annotations on all parameters and on the return value.` |
| `code-learn` | `rule_regression_tests` | E. Vi phạm quy ước tổ chức | `detail`: `RULE: add tests/test_regressions.py ... (at least 3)`. |
| `code-learn` | `rule_changelog` | E. Vi phạm quy ước tổ chức | `detail`: `RULE: record each fix in CHANGELOG.md under ... '## Unreleased'`. |
| `data-learn` | `north_q1_revenue` | D. Bỏ sót dữ liệu bẩn hoặc định dạng | `detail`: `wrong value (got 0.0)`. Vết cho thấy lệnh xử lý bằng pandas thất bại vì thiếu thư viện, nhưng tác tử không dùng cách khác để tính dữ liệu nhiều định dạng ngày/múi giờ mà ghi thẳng giá trị 0. |
| `data-learn` | `north_q1_orders` | D. Bỏ sót dữ liệu bẩn hoặc định dạng | `detail`: `wrong value (got 0)`. Tác tử không xử lý thành công các ngày `YYYY-MM-DD`, `DD/MM/YYYY` và ISO-8601 có offset trước khi đếm. |
| `data-learn` | `missing_amount_orders` | D. Bỏ sót dữ liệu bẩn hoặc định dạng | `detail`: `wrong value (got 0)`. README nêu `-999` là giá trị thiếu nhưng sau khi script thất bại, tác tử vẫn ghi 0 mà không kiểm chứng. |
| `data-learn` | `duplicate_rows_removed` | D. Bỏ sót dữ liệu bẩn hoặc định dạng | `detail`: `wrong value (got 0)`. Vết dùng `drop_duplicates()` rồi mới gọi `duplicated().sum()`, nên phép đếm luôn bằng 0. |
| `data-learn` | `rule_money_in_cents` | E. Vi phạm quy ước tổ chức | `detail`: `RULE: money values in answer.json are integer cents`. |
| `data-learn` | `rule_meta_block` | E. Vi phạm quy ước tổ chức | `detail`: `RULE: answer.json has an object meta = ...`. |
| `data-learn` | `rule_clean_csv` | E. Vi phạm quy ước tổ chức | `detail`: `RULE: write workspace/clean.csv ... amount in integer cents`. |
| `logs-learn` | `valid_structure` | B. Không kiểm chứng | `detail`: `FileNotFoundError ... workspace/errors.json`; vết kết thúc sau hai lần đọc `app.log`, không có lần ghi tệp hoặc chạy kiểm tra. |
| `logs-learn` | `entry_count` | B. Không kiểm chứng | Không có `errors.json`; vết không cho thấy tác tử tạo hay kiểm tra số entry. |
| `logs-learn` | `timestamps_utc` | B. Không kiểm chứng | Không có `errors.json`; không có bước kiểm tra chuyển đổi timestamp sang UTC. |
| `logs-learn` | `exception_fields` | B. Không kiểm chứng | Không có `errors.json`; tác tử không kiểm tra việc lấy dòng cuối traceback. |
| `logs-learn` | `repeat_counts` | B. Không kiểm chứng | Không có `errors.json`; không có bước kiểm tra các dòng `last message repeated N times`. |
| `logs-learn` | `counts_by_service` | B. Không kiểm chứng | Không có `errors.json`; không có kết quả để đối chiếu tổng `repeat_count` theo service. |
| `logs-learn` | `rule_service_names` | B. Không kiểm chứng | Check dừng ở `FileNotFoundError` trước khi có thể kiểm tra quy ước; nguyên nhân trực tiếp vẫn là tác tử không tạo và kiểm tra đầu ra. |
| `logs-learn` | `rule_sorted_errors` | B. Không kiểm chứng | Check dừng ở `FileNotFoundError`; vết không có thao tác ghi/sắp xếp `errors.json`. |
| `logs-learn` | `rule_schema_header` | B. Không kiểm chứng | Check dừng ở `FileNotFoundError`; vết không có thao tác tạo schema/header. |

Kết quả `baseline/data-learn` dùng trong bảng là lần chạy Docker hợp lệ (`error=null`, trace đầy đủ). Check `tests_not_modified` của `code-learn` được loại: vết không sửa `tests/`, và SHA-256 sau khi chuẩn hóa CRLF thành LF là `79e05f...ee00d`, đúng bằng hash mà checker yêu cầu; đây là nhiễu line-ending của checkout Windows/Docker.

Trong 21 check thất bại hợp lệ để phân loại, nhóm B chiếm đa số với 9 check, tiếp theo là E với 6, D với 4 và A với 2. Sau khi loại nhiễu line-ending, các check kỹ thuật đạt 5/17: `code-learn` đạt 4/6, `data-learn` đạt 1/5 và `logs-learn` đạt 0/6. Đây là bằng chứng phủ định rõ rằng lỗi không chỉ nằm ở quy ước ẩn; tác tử còn bỏ sót trường hợp trong đặc tả, xử lý sai dữ liệu bẩn/định dạng và kết thúc mà chưa tạo hoặc kiểm tra đầu ra. Một skill dạng checklist có thể giảm nhóm A/B/D bằng cách bắt buộc đọc README và toàn bộ docstring, lập danh sách định dạng đặc biệt, xác nhận các tệp bắt buộc tồn tại, rồi chạy checker trước khi kết thúc. Một skill riêng ghi nhớ các quy ước Acme từ phản hồi `RULE:` có thể phòng ngừa nhóm E.

## 5. Điều kiện `subagents` (Phần 2.3)

- Các subagent đã định nghĩa: `explorer` đọc tài liệu/dữ liệu và chỉ báo cáo sự thật; `implementer` thực hiện thay đổi và chạy kiểm tra; `reviewer` kiểm tra độc lập yêu cầu, trường hợp biên và hồi quy. Ba vai trò tách khám phá, thực thi và kiểm chứng để tác tử chính có thể giao phần việc phù hợp mà không trộn trách nhiệm.
- `subagent_calls` bằng 0 ở cả `code-learn`, `data-learn` và `logs-learn`. Không trace nào có tool call `task`; tác tử chính tự đọc, sửa và chạy lệnh. Với `code-learn` và `logs-learn`, mô hình có thể xem công việc là đủ trực tiếp để tự làm. `data-learn` là tác vụ nhiều bước nhưng tác tử vẫn tự viết nhiều script, cho thấy lời khuyến khích trong prompt không bảo đảm subagent sẽ được gọi.
- Không có lời giao việc hoặc báo cáo subagent để đánh giá thiếu/thừa thông tin hay việc kiểm tra báo cáo. Đây là kết quả hợp lệ, nhưng cũng có nghĩa lần chạy này chưa đo được lợi ích thực tế của ba subagent đã định nghĩa.

| Tác vụ | Baseline: điểm, token, giây | Subagents: điểm, token, giây | Chênh lệch token | Nhận xét |
|---|---:|---:|---:|---|
| `code-learn` | 0,40; 37.952; 27,0 s | 0,30; 60.090; 38,2 s | +22.138 (+58,3%) | Tốn token và thời gian hơn nhưng điểm giảm 0,10; không có lần gọi subagent. |
| `data-learn` | 0,125; 25.754; 16,5 s | 0,25; 114.211; 179,0 s | +88.457 (+343,5%) | Điểm tăng 0,125 nhưng token tăng hơn bốn lần; cả hai lần chạy đều không gọi subagent. |
| `logs-learn` | 0,00; 29.140; 187,4 s | 0,00; 29.575; 205,4 s | +435 (+1,5%) | Điểm không đổi, token và thời gian đều tăng nhẹ; không có lần gọi subagent. |

Trên cả ba tác vụ, token trung bình tăng từ 30.948,7 lên 67.958,7 (+119,6%) và thời gian trung bình tăng từ 77,0 lên 140,9 giây (+83,0%). Điểm trung bình chỉ tăng từ 0,175 lên 0,183. Vì `subagent_calls=0`, chênh lệch này không phải chi phí gọi tác tử con mà chủ yếu phản ánh nhiễu giữa các lần chạy và hành vi dài hơn của tác tử chính; chưa có bằng chứng rằng cấu hình subagents đáng với chi phí trong thí nghiệm này.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Curator được chạy 2 lần. Lần 1 sinh 3 skill và cả 3 bị xóa: `prevent-parallel-file-mutations` đề xuất lock, pause và version control thay vì tuần tự hóa các tool edit; `enforce-type-annotations` dành phần lớn nội dung cho CI, audit và đào tạo đội nhóm, không tập trung vào hành động của agent; `maintain-changelog` quá chung và không nêu cấu trúc changelog/check regression cần thiết. Lần 2 sinh 3 skill; xóa lại `prevent-parallel-file-mutations` vì vẫn lặp nguyên hướng dẫn không phù hợp. Tổng cộng có 4 lượt xóa skill qua hai lần curator (3 tên duy nhất); giữ nguyên 2 skill của lần 2 và không sửa tay nội dung.

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `enforce-type-annotations` | Tổng quát cho tác vụ sửa hoặc rà soát mã nguồn; không chứa id, tên hàm hay đáp án riêng của tác vụ học. | Đúng ở yêu cầu thêm annotation cho mọi tham số và kiểu trả về của hàm public. Tuy nhiên các bước về CI, audit, coding standards và đào tạo đội nhóm thừa, không khả thi trong một lượt agent và có thể làm phình phạm vi công việc. | 13 dòng. Description: “Use this skill to ensure all public functions have complete type annotations.” Tình huống kích hoạt đúng nhưng khá hẹp. `skills_read`: code=0, data=0, logs=0; giá trị của code không kết luận được do recursion làm mất trace. |
| `maintain-changelog-and-test-requirements` | Tổng quát cho tác vụ thay đổi code; không lặp tên hàm hay đáp án của tác vụ học. | Đúng về nguyên tắc mỗi bug fix cần regression test và changelog. Chưa đủ chính xác cho quy ước Acme vì không nêu `## Unreleased`, mẫu `- fix(...)` và `tests/test_regressions.py`; bước “mỗi bug một file test riêng” còn có thể tạo cấu trúc thừa. | 13 dòng. Description: “Use this skill to ensure that all changes are documented and tested appropriately.” Rộng và dễ kích hoạt ở task code. `skills_read`: code=0, data=0, logs=0; giá trị của code không kết luận được do recursion. |

Kết quả Phần 3.4:

| Tác vụ | Baseline | `skills-auto` | `skills_read` | Bằng chứng từ vết |
|---|---:|---:|---:|---|
| `code-learn` | 4/10; 37.952 token | 0/10; 179.720 token | 0 | Lần chạy bị `GraphRecursionError` ở giới hạn 60; runner đặt messages rỗng nên trace và bộ đếm tool/skill bị mất. Không thể kết luận agent có đọc skill hay không. |
| `data-learn` | 1/8; 25.754 token | 1/8; 40.513 token | 0 | Trace không có `read_file` dưới `skills/`; hai description về code không phù hợp tác vụ dữ liệu. Skill không tác động, điểm không đổi. |
| `logs-learn` | 0/9; 29.140 token | 0/9; 30.768 token | 0 | Trace chỉ đọc hai phần của `app.log`, không đọc skill và không tạo `errors.json`; điểm không đổi. |

Hai run không lỗi cho thấy skill không được chọn đọc và không có quy tắc nào được áp dụng. Với `code-learn`, cả hai description đáng lẽ phù hợp nhưng lỗi recursion khiến vết tối thiểu bị mất; do đó `skills_read=0` không phải bằng chứng chắc chắn về hành vi bên trong. Trung bình điểm giảm từ 0,175 xuống 0,0417, còn token trung bình tăng từ 30.948,7 lên 83.667. Kết quả này không chứng minh skill gây suy giảm vì chỉ có một lần chạy và `code-learn` không hoàn tất do giới hạn recursion, nhưng không có bằng chứng rằng hai skill tự sinh đã giúp tác vụ học.

Cả ba run ghi cùng `skills_sha256=541e22c2...0ccefe`, trùng với hash tính lại trong Docker, và đều có `skills_modified=false`; vì vậy chúng dùng cùng bộ skill và agent không sửa skill khi chạy. Hash tính trực tiếp trên Windows khác do `hash_skills` đưa dấu phân cách đường dẫn của hệ điều hành vào dữ liệu băm, nên mọi kiểm tra freeze/hash của các kết quả Docker cần được chạy trong Docker.

## 7. Kết quả so sánh (Phần 4.3, 4.4)

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 4/10 | 3/10 | 1/10 |
| data-learn | 1/8 | 2/8 | 3/8 |
| logs-learn | 0/9 | 0/9 | 1/9 |
| code-eval | 1/11 | 1/11 | 4/11 |
| data-eval | 0/9 | 1/9 | 3/9 |
| logs-eval | 1/10 | 1/10 | 1/10 |
| **Mean score - learning tasks** | 0.18 | 0.18 | 0.20 |
| **Mean score - evaluation tasks** | 0.06 | 0.10 | 0.27 |
| **Mean tokens per run** | 60,638 | 85,341 | 74,274 |
| **Runs that read a skill** | 0/6 | 0/6 | 0/6 |

Kết quả `python scripts/check_breakdown.py` sau khi đóng băng:

```text
condition     role    technical  house rules  mean tokens  read a skill
baseline      eval      2/18         0/12          90,327      0/3
baseline      learn     5/18         0/9           30,948      0/3
subagents     eval      3/18         0/12         102,723      0/3
subagents     learn     5/18         0/9           67,958      0/3
skills-auto   eval      8/18         0/12          65,101      0/3
skills-auto   learn     5/18         0/9           83,446      0/3
```

`python scripts/verify_freeze.py` trong container trả về `checked 6 runs of skill conditions: OK`. Cả sáu run chính thức của `skills-auto` có cùng `skills_sha256=541e22c2...0ccefe`, bắt đầu sau tag `freeze` và ghi `skills_modified=false`. Không run nào trong ba điều kiện đọc skill (`skills_read=0/6`), vì vậy chênh lệch điểm giữa các điều kiện chưa thể quy trực tiếp cho việc áp dụng nội dung skill.

Bảy run ban đầu gặp `GraphRecursionError` ở giới hạn 60 và đã được retry đúng một lần theo GUIDE. Bản ban đầu được giữ trong `results-first-attempt/`; bảng trên dùng bản retry chính thức trong `results/`:

| Điều kiện / tác vụ | Lần đầu | Retry | Trạng thái retry |
|---|---:|---:|---|
| `baseline/code-eval` | 0/11 | 1/11 | Vẫn `GraphRecursionError` |
| `subagents/code-eval` | 0/11 | 1/11 | Vẫn `GraphRecursionError` |
| `subagents/data-eval` | 0/9 | 1/9 | Hoàn tất, không lỗi |
| `skills-auto/code-learn` | 4/10 | 1/10 | Vẫn `GraphRecursionError` |
| `skills-auto/data-eval` | 0/9 | 3/9 | Hoàn tất, không lỗi |
| `skills-auto/data-learn` | 0/8 | 3/8 | Hoàn tất, không lỗi |
| `skills-auto/logs-eval` | 0/10 | 1/10 | Hoàn tất, không lỗi |

Ba retry vẫn lỗi được giữ nguyên, không tăng `recursion_limit` sau khi đóng băng để không thay đổi cấu hình giữa các điều kiện. Các run có lỗi vẫn được runner chấm trên trạng thái workspace tại thời điểm dừng; vì vậy điểm của chúng được báo cáo nhưng phải được xem là kết quả bị kiểm duyệt bởi giới hạn vòng lặp, không tương đương một lần hoàn tất bình thường.

## 8. Phân tích

1. **Điểm học và điểm đánh giá.** Trên tác vụ học, điểm trung bình chưa làm tròn là `baseline=0,175`, `subagents=0,183` và `skills-auto=0,195`; hai điều kiện sau chỉ tăng lần lượt `0,008` và `0,020` so với baseline. Trên tác vụ đánh giá, các giá trị là `0,064`, `0,101` và `0,266`, nên subagents tăng `0,037` còn skills-auto tăng `0,202`. Không có điều kiện nào tăng trên tập học nhưng giảm trên tập đánh giá. H1 bị bác bỏ vì subagents cao hơn baseline trên eval; H2 bị bác bỏ vì skills-auto cao nhất thay vì thấp hơn baseline; H3 đúng với baseline và subagents nhưng sai với skills-auto, có eval cao hơn learn. Tuy nhiên, ba kết luận này chỉ mô tả tương quan của các run: subagent không được gọi, skill không được đọc và ba run chính thức vẫn bị recursion error.

2. **Check kỹ thuật và quy ước.** Trên tập học, baseline, subagents và skills-auto lần lượt đạt `5/18`, `5/18`, `5/18` check kỹ thuật; trên tập đánh giá là `2/18`, `3/18`, `8/18`. Cả ba điều kiện đều đạt `0/9` check quy ước ở tập học và `0/12` ở tập đánh giá. Do đó phần tăng của skills-auto chỉ xuất hiện ở check kỹ thuật, nhưng không có bằng chứng skill gây ra mức tăng: `skills_read=0` ở cả sáu run. Các quy ước mới của eval không được giúp; ngoài việc skill không được đọc, bộ skill còn thiếu quy ước mới như `rule_version_bump` và không mô tả chính xác schema/quy tắc của nhóm data, logs.

3. **Cơ chế từ vết.** Không có check nào có thể được khẳng định là “được skill giúp đạt”. Chẳng hạn `skills-auto/code-eval` đạt `visible_suite_passes`, `billable_blocks_round_up`, `add_slot_no_shared_state` và `negative_minutes_rejected`; trace cho thấy agent trực tiếp đọc mã, sửa nhiều lần và chạy `pytest`, trong khi không có lần đọc `/skills/.../SKILL.md`, nên đây là hành vi tự thân của agent chứ không phải tác động của skill. Ngược lại, cùng run đó trượt cả `rule_type_hints`, `rule_regression_tests`, `rule_changelog` và `rule_version_bump`; đây là ví dụ trực tiếp rằng hai skill liên quan không giúp khi cơ chế chọn skill không kích hoạt. Tương tự, `data-eval` đạt ba check kỹ thuật sau khi đọc `orders.json`, README và chạy script một lần, nhưng không đọc skill và trượt toàn bộ bốn check `rule_`.

4. **Chi phí.** Token trung bình trên sáu run là baseline `60.638`, subagents `85.341` và skills-auto `74.274`; subagents tốn hơn baseline `40,7%`, skills-auto tốn hơn `22,5%`. Nếu lấy điểm chuẩn hóa trung bình chia token, số điểm trên 100.000 token lần lượt xấp xỉ `0,197`, `0,166`, `0,310`; chỉ riêng eval là `0,070`, `0,098`, `0,408`. Skills-auto có hiệu quả quan sát tốt nhất, nhưng không thể coi đó là lợi ích của skill vì `skills_read=0/6`. Subagents có hiệu quả tổng thể thấp nhất và `subagent_calls=0/6`, nên thí nghiệm này không cung cấp bằng chứng rằng đa tác tử đáng chi phí; chênh lệch chủ yếu là nhiễu giữa các lượt của agent chính.

5. **Rò rỉ và quá khớp.** Không thấy dấu hiệu rò rỉ eval trong hai skill: chúng không chứa id/tên tệp riêng của eval, curator chỉ nhận feedback và phần cuối trace của `baseline/*-learn`, `validate_skill` chặn marker eval, và lịch sử Git chứng minh commit giả thuyết cùng skill đã có trước tag `freeze` và trước các run eval. Hai skill tập trung vào type annotation, regression test và changelog được rút từ feedback learn, nên có nguy cơ quá khớp về phạm vi; chúng không bao phủ quy ước data/log hoặc `rule_version_bump`. Dù vậy, vì không run nào đọc skill, dữ liệu hiện tại chỉ chứng minh khoảng trống bao phủ và kích hoạt, chưa đủ để kết luận quá khớp trong hành vi thực tế.

6. **Nhiễu giữa hai lần chạy cùng bộ skill.** Ở Phần 3.4, `skills-auto` đạt lần lượt `0/10`, `1/8`, `0/9`; sau đóng băng và retry đạt `1/10`, `3/8`, `1/9`. Chênh lệch theo tác vụ là `+0,100`, `+0,250`, `+0,111`, làm điểm học trung bình tăng từ `0,0417` lên `0,1954` (`+0,1537`) dù hash skill giống nhau, `skills_modified=false` và không lần nào ghi nhận đọc skill. Ngay trong hai attempt sau đóng băng, `code-learn` đổi từ `4/10` xuống `1/10`, còn `data-learn` từ `0/8` lên `3/8`. Biên độ này lớn hơn nhiều chênh lệch baseline–subagents, nên các khác biệt nhỏ trong bảng không đáng tin nếu không lặp nhiều seed; cả lợi thế eval của skills-auto cũng chỉ nên xem là kết quả quan sát, không phải ước lượng nhân quả.

## 9. Hạn chế và tính hợp lệ

1. **Cỡ mẫu nhỏ và tác vụ nhân tạo:** mỗi vai trò chỉ có ba tác vụ thuộc code, data và logs, với quy ước do giảng viên thiết kế. Điểm trung bình vì vậy nhạy với một task và không đại diện chắc chắn cho repository hay quy ước tổ chức ngoài thực tế.
2. **Ít lần lặp và nhiễu lớn:** mỗi ô chính thức chỉ giữ một run; bảy run phải retry và cùng bộ skill cho chênh lệch điểm học `0,154`. Điều này làm các chênh lệch nhỏ, đặc biệt baseline so với subagents, không đủ độ tin cậy thống kê.
3. **Kết quả bị kiểm duyệt bởi recursion limit:** ba run chính thức vẫn gặp `GraphRecursionError`; khi bắt exception, runner không còn message để đếm tool/skill call dù workspace vẫn được chấm. Điểm và các bộ đếm bằng 0 của những run này có thể không phản ánh đầy đủ hành vi trước lúc dừng.
4. **Can thiệp không được kích hoạt:** `subagent_calls=0/6` và `skills_read=0/6`. Vì vậy so sánh hiện tại chủ yếu đo nhiễu giữa các lượt của agent chính dưới prompt/cấu hình khác nhau, không kiểm định trực tiếp hiệu quả của delegation hay nội dung skill.
5. **Một mô hình và một cấu hình:** toàn bộ thí nghiệm dùng `gpt-4o-mini`, nhiệt độ 0 và giới hạn 60. Kết luận không thể suy rộng sang mô hình mạnh hơn, nhà cung cấp khác hoặc chiến lược giới hạn vòng lặp khác; nhiệt độ 0 cũng không loại bỏ hoàn toàn tính bất định của API/tool calling.

## 10. Kết luận

Harness, curator và quy trình đóng băng đã hoạt động đúng, với `verify_freeze.py` báo OK cho sáu run skills-auto. Trong lần đo chính thức, skills-auto có điểm eval trung bình cao nhất (`0,266`) so với subagents (`0,101`) và baseline (`0,064`), đồng thời có hiệu quả điểm/token quan sát cao nhất. Tuy nhiên, không run nào đọc skill, không run subagents nào gọi tác tử con và mọi check quy ước đều thất bại, nên không thể quy lợi thế đó cho hai cơ chế đang nghiên cứu. Nhiễu giữa các lần chạy cùng bộ skill (`+0,154` điểm học trung bình) cùng ba recursion error còn lại làm độ chắc chắn của kết luận thấp. Bước tiếp theo nên cải thiện description/routing để bắt buộc đọc skill và tiêu chí giao việc cho subagent, rồi lặp mỗi cấu hình ít nhất ba lần với giới hạn vòng lặp thống nhất được chốt trước khi freeze.

## Phụ lục

- Lệnh chính đã chạy theo thứ tự:

```bash
pytest tests/test_01_provided.py tests/test_02_agent.py tests/test_03_runner.py
python -m lab.runner --condition baseline --tasks code-learn logs-learn
python -m lab.runner --condition subagents --tasks learn
pytest tests/test_04_curator.py
python -m lab.curator
python -m lab.curator
python -m lab.runner --condition skills-auto --tasks learn
git commit -m "hypotheses"
git commit --allow-empty -m "freeze skills"
git tag freeze
python -m lab.runner --condition baseline --tasks eval
python -m lab.runner --condition subagents --tasks eval
python -m lab.runner --condition skills-auto --tasks all
python -m lab.runner --condition baseline --tasks code-eval --results results-rerun
python -m lab.runner --condition subagents --tasks code-eval data-eval --results results-rerun
python -m lab.runner --condition skills-auto --tasks code-learn data-eval data-learn logs-eval --results results-rerun
python scripts/verify_freeze.py
python -m lab.compare
python scripts/check_breakdown.py
pytest
```

- Các lệnh Python được chạy trong container tại `/lab`; các retry dùng cùng model/config và chỉ thay API key khi key cũ bị giới hạn.
- Thử thách mở rộng: không thực hiện; `results-first-attempt/` chỉ là bản lưu bằng chứng trước retry, không phải Phần 6e vì mỗi lỗi chỉ được retry một lần.
- Ghi chú: Git trong container được cài tạm để chạy nguyên bản `verify_freeze.py`; việc này không thay đổi source hay image đã commit. `results-docker/` là artifact cục bộ cũ, không thuộc kết quả nộp.
