# kr-business-day

한국 공휴일(2026~2027)을 반영해 영업일을 계산하는 단일 파일 파이썬 도구 겸 에이전트 스킬입니다. 외부 패키지 없이 표준 라이브러리만 사용합니다.

## 무엇을 하나

- 특정 날짜가 영업일인지 판정 (주말·공휴일·대체공휴일 반영)
- 기준일로부터 N영업일 뒤/앞 날짜 계산
- 두 날짜 사이의 영업일 수 계산
- 내장 자체검사(70개 검사)로 경계값 동작 확인

## 설치

설치 과정이 없습니다. `kr_business_day.py` 파일 하나만 내려받아 실행하면 됩니다.

```bash
# Python 3.9 이상
python kr_business_day.py --selftest
```

## 사용 예시

```bash
# 2026-10-05가 영업일인지 확인
python kr_business_day.py --is-business-day 2026-10-05

# 2026-09-30 기준 5영업일 뒤
python kr_business_day.py --add 2026-09-30 5

# 두 날짜 사이 영업일 수
python kr_business_day.py --count 2026-09-01 2026-09-30
```

파이썬 코드에서 직접 쓰는 경우:

```python
from kr_business_day import is_business_day, add_business_days, count_business_days
from datetime import date

is_business_day(date(2026, 10, 5))
add_business_days(date(2026, 9, 30), 5)
count_business_days(date(2026, 9, 1), date(2026, 9, 30))
```

실제 인자 이름과 출력 형식은 `python kr_business_day.py --help`로 확인하세요.

## 한계 (반드시 확인)

- 공휴일 표는 **2026~2027년 43건**만 내장되어 있습니다. 이 범위 밖 날짜는 주말만 제외하므로 결과가 틀릴 수 있습니다.
- 임시공휴일은 정부 발표 시점에 따라 달라집니다. 발표된 임시공휴일은 표에 직접 추가해야 합니다.
- 금융결제원/증권 결제일 등 기관별 특수 휴장일은 반영하지 않습니다.
- 세무·법무 기한 계산에 쓸 경우 최종 확인은 관련 기관 공식 안내를 따르세요.

## 검증 상태

- 내장 `--selftest` 70개 검사(주말, 연휴, 대체공휴일, 월말 경계 포함) 통과 기록이 있습니다.
- 팀 내 동료가 전문을 읽고 독립 실행으로 확인했습니다.
- 이 검증은 내장된 2026~2027 공휴일 표를 전제로 한 동작 확인이며, 공휴일 표 자체가 미래에 변경되지 않음을 보장하지 않습니다.

## 권리·이용 조건

직접 작성한 코드와 문서입니다. LICENSE 파일의 조건에 따라 자유롭게 사용·수정·재배포할 수 있습니다. 무료 배포이며 결제 의무는 없습니다.
