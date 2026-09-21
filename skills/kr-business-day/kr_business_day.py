#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kr_business_day.py — 한국 공휴일/영업일(D+N) 계산기 (2026~2027)

왜 필요한가
-----------
한국 실무에서 '영업일 기준 3일 내 발송', '세금계산서 D+5영업일' 같은 마감일을
손으로 세다 보면 주말은 빼도 대체공휴일(월요일)을 빠뜨려 하루가 어긋난다.
이 파일은 2026~2027년 관공서 공휴일 표를 내장해 그 계산을 대신한다.

중요한 한계 (반드시 읽을 것)
---------------------------
1) 내장 표는 2026-01-01 ~ 2027-12-31 범위에서만 동작한다. 범위 밖은 ValueError.
2) 설날/추석/부처님오신날은 음력 기반이며, 이 파일은 음력을 계산하지 않고
   널리 통용되는 날짜를 '표'로 적어둔 것이다. 정부가 임시공휴일을 추가로
   지정하거나 관보 확정치가 다르면 HOLIDAYS 표를 직접 고쳐야 한다.
   법적 효력이 있는 마감(신고·납부 기한)은 반드시 관보/국세청 공고로 재확인하라.
3) 토요일은 공휴일이 아니지만 이 계산기는 '영업일'에서 제외한다(주5일 가정).
   토요일도 영업하는 업종이면 saturday_is_business=True 로 호출한다.
4) 대체공휴일은 '계산'하지 않고 확정 날짜를 표에 직접 넣었다. 대체공휴일
   적용 대상은 설날·추석·삼일절·어린이날·부처님오신날·광복절·개천절·한글날·
   성탄절이며 현충일은 대상이 아니다(그래서 토/일에 걸려도 대체일이 없다).

사용법
------
  python kr_business_day.py --selftest
  python kr_business_day.py --add 2026-09-23 5
  python kr_business_day.py --count 2026-09-01 2026-09-30
  python kr_business_day.py --next 2026-08-15
  python kr_business_day.py --list 2026

라이선스: 직접 작성. 자유 사용/수정/재배포 가능(출처 표기 환영), 무보증.
"""

import sys
from datetime import date, timedelta

WEEKDAY_KO = ["월", "화", "수", "목", "금", "토", "일"]

# (날짜, 명칭, 표기 요일) — 표기 요일은 오타 검출용으로 selftest에서 대조한다.
HOLIDAYS = {
    # ---- 2026 ----
    "2026-01-01": ("신정", "목"),
    "2026-02-16": ("설날 연휴", "월"),
    "2026-02-17": ("설날", "화"),
    "2026-02-18": ("설날 연휴", "수"),
    "2026-03-01": ("삼일절", "일"),
    "2026-03-02": ("삼일절 대체공휴일", "월"),
    "2026-05-05": ("어린이날", "화"),
    "2026-05-24": ("부처님오신날", "일"),
    "2026-05-25": ("부처님오신날 대체공휴일", "월"),
    "2026-06-06": ("현충일(토, 대체 없음)", "토"),
    "2026-08-15": ("광복절", "토"),
    "2026-08-17": ("광복절 대체공휴일", "월"),
    "2026-09-24": ("추석 연휴", "목"),
    "2026-09-25": ("추석", "금"),
    "2026-09-26": ("추석 연휴", "토"),
    "2026-09-28": ("추석 대체공휴일", "월"),
    "2026-10-03": ("개천절", "토"),
    "2026-10-05": ("개천절 대체공휴일", "월"),
    "2026-10-09": ("한글날", "금"),
    "2026-12-25": ("성탄절", "금"),
    # ---- 2027 ----
    "2027-01-01": ("신정", "금"),
    "2027-02-05": ("설날 연휴", "금"),
    "2027-02-06": ("설날", "토"),
    "2027-02-07": ("설날 연휴", "일"),
    "2027-02-08": ("설날 대체공휴일", "월"),
    "2027-02-09": ("설날 대체공휴일", "화"),
    "2027-03-01": ("삼일절", "월"),
    "2027-05-05": ("어린이날", "수"),
    "2027-05-13": ("부처님오신날", "목"),
    "2027-06-06": ("현충일(일, 대체 없음)", "일"),
    "2027-08-15": ("광복절", "일"),
    "2027-08-16": ("광복절 대체공휴일", "월"),
    "2027-09-14": ("추석 연휴", "화"),
    "2027-09-15": ("추석", "수"),
    "2027-09-16": ("추석 연휴", "목"),
    "2027-10-03": ("개천절", "일"),
    "2027-10-04": ("개천절 대체공휴일", "월"),
    "2027-10-09": ("한글날", "토"),
    "2027-10-11": ("한글날 대체공휴일", "월"),
    "2027-12-25": ("성탄절", "토"),
    "2027-12-27": ("성탄절 대체공휴일", "월"),
}

SUPPORTED_MIN = date(2026, 1, 1)
SUPPORTED_MAX = date(2027, 12, 31)


class OutOfRange(ValueError):
    pass


def parse_date(s):
    """'YYYY-MM-DD' 또는 'YYYYMMDD' 문자열을 date로."""
    if isinstance(s, date):
        return s
    t = str(s).strip().replace(".", "-").replace("/", "-")
    if len(t) == 8 and t.isdigit():
        t = "%s-%s-%s" % (t[0:4], t[4:6], t[6:8])
    parts = t.split("-")
    if len(parts) != 3:
        raise ValueError("날짜 형식 오류: %r (예: 2026-09-23)" % s)
    y, m, d = (int(p) for p in parts)
    return date(y, m, d)


def _check_range(d):
    if d < SUPPORTED_MIN or d > SUPPORTED_MAX:
        raise OutOfRange(
            "지원 범위(%s ~ %s) 밖입니다: %s. 표를 확장해야 합니다."
            % (SUPPORTED_MIN, SUPPORTED_MAX, d)
        )


def holiday_name(d):
    """공휴일이면 명칭, 아니면 None. (토/일 자체는 공휴일로 보지 않음)"""
    d = parse_date(d)
    _check_range(d)
    item = HOLIDAYS.get(d.isoformat())
    return item[0] if item else None


def is_holiday(d):
    return holiday_name(d) is not None


def is_business_day(d, saturday_is_business=False):
    """영업일이면 True. 기본: 월~금 중 공휴일이 아닌 날."""
    d = parse_date(d)
    _check_range(d)
    wd = d.weekday()  # 0=월 ... 5=토, 6=일
    if wd == 6:
        return False
    if wd == 5 and not saturday_is_business:
        return False
    return not is_holiday(d)


def next_business_day(d, saturday_is_business=False, include_self=False):
    """d가 영업일이 아니면 그 다음 영업일. include_self=True면 d도 후보."""
    cur = parse_date(d)
    _check_range(cur)
    if include_self and is_business_day(cur, saturday_is_business):
        return cur
    cur += timedelta(days=1)
    while True:
        _check_range(cur)
        if is_business_day(cur, saturday_is_business):
            return cur
        cur += timedelta(days=1)


def prev_business_day(d, saturday_is_business=False, include_self=False):
    cur = parse_date(d)
    _check_range(cur)
    if include_self and is_business_day(cur, saturday_is_business):
        return cur
    cur -= timedelta(days=1)
    while True:
        _check_range(cur)
        if is_business_day(cur, saturday_is_business):
            return cur
        cur -= timedelta(days=1)


def add_business_days(start, n, saturday_is_business=False):
    """start로부터 n영업일 뒤(또는 음수면 앞) 날짜.

    규칙: 시작일 자체는 세지 않는다(D+1영업일 = 시작일 다음 영업일).
    n=0이면 start가 영업일이면 그대로, 아니면 다음 영업일로 보정한다.
    """
    cur = parse_date(start)
    _check_range(cur)
    n = int(n)
    if n == 0:
        return next_business_day(cur, saturday_is_business, include_self=True)
    step = 1 if n > 0 else -1
    remaining = abs(n)
    while remaining > 0:
        cur += timedelta(days=step)
        _check_range(cur)
        if is_business_day(cur, saturday_is_business):
            remaining -= 1
    return cur


def business_days_between(start, end, saturday_is_business=False,
                          include_start=False, include_end=True):
    """두 날짜 사이 영업일 수. 기본은 (start, end] 구간."""
    a = parse_date(start)
    b = parse_date(end)
    if a > b:
        a, b = b, a
    _check_range(a)
    _check_range(b)
    count = 0
    cur = a
    while cur <= b:
        if cur == a and not include_start:
            cur += timedelta(days=1)
            continue
        if cur == b and not include_end:
            break
        if is_business_day(cur, saturday_is_business):
            count += 1
        cur += timedelta(days=1)
    return count


def deadline(start, n_business_days, saturday_is_business=False):
    """마감일 안내용 dict. 사람에게 그대로 보여줄 수 있는 문장 포함."""
    s = parse_date(start)
    due = add_business_days(s, n_business_days, saturday_is_business)
    skipped = []
    cur = s + timedelta(days=1)
    while cur <= due:
        if not is_business_day(cur, saturday_is_business):
            label = holiday_name(cur) or ("주말(%s)" % WEEKDAY_KO[cur.weekday()])
            skipped.append("%s %s" % (cur.isoformat(), label))
        cur += timedelta(days=1)
    return {
        "start": s.isoformat(),
        "business_days": int(n_business_days),
        "due": due.isoformat(),
        "due_weekday": WEEKDAY_KO[due.weekday()],
        "calendar_days": (due - s).days,
        "skipped": skipped,
        "text": "%s 기준 %d영업일 마감은 %s(%s)입니다. 달력일로 %d일이며 제외된 날 %d일: %s"
                % (s.isoformat(), int(n_business_days), due.isoformat(),
                   WEEKDAY_KO[due.weekday()], (due - s).days, len(skipped),
                   ", ".join(skipped) if skipped else "없음"),
    }


def list_holidays(year):
    year = int(year)
    out = []
    for k in sorted(HOLIDAYS):
        if k.startswith("%04d-" % year):
            d = parse_date(k)
            out.append((k, WEEKDAY_KO[d.weekday()], HOLIDAYS[k][0]))
    return out


# ----------------------------------------------------------------------
# 자체 검증
# ----------------------------------------------------------------------
def selftest():
    fails = []
    checks = 0

    def eq(got, want, label):
        nonlocal checks
        checks += 1
        g = got.isoformat() if isinstance(got, date) else got
        if g != want:
            fails.append("%s -> got %r, want %r" % (label, g, want))

    # 1) 표 무결성: 기재 요일과 실제 요일 일치 (오타/날짜 착오 검출)
    for k, (name, wd) in sorted(HOLIDAYS.items()):
        d = parse_date(k)
        checks += 1
        if WEEKDAY_KO[d.weekday()] != wd:
            fails.append("표 요일 불일치 %s %s: 실제 %s, 표기 %s"
                         % (k, name, WEEKDAY_KO[d.weekday()], wd))
        if not (SUPPORTED_MIN <= d <= SUPPORTED_MAX):
            fails.append("표 범위 이탈 %s" % k)

    # 2) 주말 경계
    eq(is_business_day("2026-09-19"), False, "2026-09-19(토) 영업일아님")
    eq(is_business_day("2026-09-20"), False, "2026-09-20(일) 영업일아님")
    eq(is_business_day("2026-09-21"), True, "2026-09-21(월) 영업일")
    eq(is_business_day("2026-09-19", saturday_is_business=True), True,
       "토요근무 옵션")

    # 3) 설날 연휴(2026-02-16~18) 건너뛰기: 금(2/13) +1영업일 = 2/19(목)
    eq(add_business_days("2026-02-13", 1), "2026-02-19", "설날연휴 건너뛰기")
    eq(is_business_day("2026-02-17"), False, "설날 당일")

    # 4) 대체공휴일: 2026-03-01(일)의 대체 3/2(월) → 2/27(금)+1영업일=3/3(화)
    eq(add_business_days("2026-02-27", 1), "2026-03-03", "삼일절 대체 반영")
    eq(holiday_name("2026-03-02"), "삼일절 대체공휴일", "대체공휴일 명칭")

    # 5) 광복절(토)+대체(월): 8/14(금)+1영업일 = 8/18(화)
    eq(add_business_days("2026-08-14", 1), "2026-08-18", "광복절 대체 반영")

    # 6) 추석 연휴+대체(9/24,25,26,28): 9/23(수)+1영업일 = 9/29(화)
    eq(add_business_days("2026-09-23", 1), "2026-09-29", "추석 대체 반영")
    eq(add_business_days("2026-09-23", 3), "2026-10-01", "추석 후 3영업일")

    # 7) 현충일은 대체공휴일이 없다 (2026-06-06 토) → 6/5(금)+1 = 6/8(월)
    eq(add_business_days("2026-06-05", 1), "2026-06-08", "현충일 대체 없음")

    # 8) 월말/월경계: 2026-01-30(금) +1영업일 = 2026-02-02(월)
    eq(add_business_days("2026-01-30", 1), "2026-02-02", "월말 넘김")
    # 연말연시: 2026-12-31(목) +1영업일 = 2027-01-04(월) (1/1 금 신정, 1/2 토)
    eq(add_business_days("2026-12-31", 1), "2027-01-04", "연말 넘김")

    # 9) 2027 설날 대체 2일(2/8,2/9): 2/4(목)+1영업일 = 2/10(수)
    eq(add_business_days("2027-02-04", 1), "2027-02-10", "2027 설날 대체 2일")

    # 10) 성탄절 토요일 → 12/27 대체: 2027-12-24(금)+1영업일 = 12/28(화)
    eq(add_business_days("2027-12-24", 1), "2027-12-28", "성탄 대체 반영")

    # 11) n=0 보정 / 음수 / 역산 일관성
    eq(add_business_days("2026-08-15", 0), "2026-08-18", "n=0 휴일 보정")
    eq(add_business_days("2026-09-21", 0), "2026-09-21", "n=0 영업일 유지")
    eq(add_business_days("2026-09-29", -1), "2026-09-23", "음수 역산")
    eq(prev_business_day("2026-09-28"), "2026-09-23", "이전 영업일")
    eq(next_business_day("2026-09-26"), "2026-09-29", "다음 영업일")

    # 12) 구간 영업일 수: 2026-09-01 ~ 09-30
    #     9월 평일 22일(9/1~9/30 중 월~금) - 공휴일 평일분(9/24목,9/25금,9/28월)=3
    #     (start 제외, end 포함) → 9/1 제외하면 평일 21 - 3 = 18
    eq(business_days_between("2026-09-01", "2026-09-30"), 18, "9월 영업일 수")
    eq(business_days_between("2026-09-01", "2026-09-30", include_start=True),
       19, "9월 영업일 수(시작 포함)")

    # 13) 범위 밖은 오류
    checks += 1
    try:
        is_business_day("2025-12-31")
        fails.append("범위 밖인데 예외가 없음(2025-12-31)")
    except OutOfRange:
        pass
    checks += 1
    try:
        add_business_days("2027-12-30", 20)
        fails.append("범위 초과 누적인데 예외가 없음")
    except OutOfRange:
        pass

    # 14) deadline 결과 구조
    r = deadline("2026-09-23", 3)
    eq(r["due"], "2026-10-01", "deadline due")
    checks += 1
    if len(r["skipped"]) != 5:  # 9/24,25,26,27(일),28
        fails.append("deadline skipped 개수: got %d, want 5 (%s)"
                     % (len(r["skipped"]), r["skipped"]))

    # 15) 입력 형식 허용
    eq(parse_date("20260923"), "2026-09-23", "YYYYMMDD 파싱")
    eq(parse_date("2026.09.23"), "2026-09-23", "점 구분 파싱")

    print("checks=%d fails=%d" % (checks, len(fails)))
    for f in fails:
        print("FAIL: " + f)
    print("RESULT: " + ("PASS" if not fails else "FAIL"))
    return 0 if not fails else 1


def usage():
    print(__doc__.strip())


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        usage()
        return 0
    cmd = argv[1]
    try:
        if cmd == "--selftest":
            return selftest()
        if cmd == "--add" and len(argv) >= 4:
            r = deadline(argv[2], int(argv[3]))
            print(r["text"])
            return 0
        if cmd == "--next" and len(argv) >= 3:
            d = next_business_day(argv[2], include_self=True)
            print("%s(%s)" % (d.isoformat(), WEEKDAY_KO[d.weekday()]))
            return 0
        if cmd == "--count" and len(argv) >= 4:
            n = business_days_between(argv[2], argv[3])
            print("%s ~ %s 영업일 %d일(시작일 제외, 종료일 포함)"
                  % (argv[2], argv[3], n))
            return 0
        if cmd == "--list" and len(argv) >= 3:
            for k, wd, name in list_holidays(argv[2]):
                print("%s(%s) %s" % (k, wd, name))
            return 0
    except (ValueError, OutOfRange) as e:
        print("오류: %s" % e)
        return 2
    usage()
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
