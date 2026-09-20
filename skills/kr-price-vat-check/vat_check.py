#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kr-price-vat-check 검증 도구 (v2 초안)

idea_key: kr price vat check skill v1

목적
----
한국 견적서/가격표 텍스트에서 '소계, 부가세, 합계' 숫자를 뽑아
부가세 10% 규칙과 내부 정합성을 기계적으로 점검한다.
SKILL.md(지침)만으로는 사람이 눈으로 계산해야 하므로,
실제 반복 작업을 줄이는 실행 코드를 덧붙인 것이 v2의 차이다.

한계(과장 금지)
----------------
- 정규식 기반이므로 표 형식이 복잡하거나 통화기호/단위가 섞이면 놓칠 수 있다.
- 세법 자문이 아니다. 면세·영세율·간이과세는 판정하지 않으며,
  '면세'/'영세율' 단어가 보이면 판정을 보류(SKIP)한다.
- 총액표시제 위반 여부의 법적 판단이 아니라 표기 일관성 점검이다.

사용
----
  python3 vat_check.py --text "소계 65,000원 부가세 6,500원 합계 71,500원"
  python3 vat_check.py --file quote.txt
  python3 vat_check.py --self-test

종료코드: 0=문제없음/보류, 1=불일치 발견, 2=입력 오류
"""
import argparse
import re
import sys
from decimal import Decimal, ROUND_HALF_UP

VAT_RATE = Decimal("0.10")

LABELS = {
    "subtotal": ["소계", "공급가액", "공급가", "과세표준"],
    "vat": ["부가세", "부가가치세", "VAT", "세액"],
    "total": ["합계", "총액", "총 금액", "총금액", "청구금액"],
}
EXEMPT_WORDS = ["면세", "영세율", "간이과세"]
NUM = r"([0-9][0-9,\.]*)"


def parse_amount(raw):
    s = raw.replace(",", "").rstrip(".")
    if not s:
        return None
    try:
        return Decimal(s)
    except Exception:
        return None


def find_amount(text, keywords):
    for kw in keywords:
        pat = re.compile(re.escape(kw) + r"[^0-9\-]{0,12}" + NUM)
        m = pat.search(text)
        if m:
            val = parse_amount(m.group(1))
            if val is not None:
                return val, kw
    return None, None


def round_won(value):
    """원 단위 반올림(사사오입, ROUND_HALF_UP)."""
    return value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def check(text):
    """반환: (status, findings)  status in {ok, mismatch, skip, insufficient}"""
    findings = []
    for w in EXEMPT_WORDS:
        if w in text:
            findings.append(f"SKIP: '{w}' 표기가 있어 10% 일반과세 판정을 보류한다.")
            return "skip", findings

    sub, sub_kw = find_amount(text, LABELS["subtotal"])
    vat, vat_kw = find_amount(text, LABELS["vat"])
    tot, tot_kw = find_amount(text, LABELS["total"])

    found = [("소계", sub, sub_kw), ("부가세", vat, vat_kw), ("합계", tot, tot_kw)]
    for name, val, kw in found:
        if val is None:
            findings.append(f"MISSING: {name} 항목을 찾지 못했다.")
        else:
            findings.append(f"FOUND: {name}(표기 '{kw}') = {val}")

    known = [v for _, v, _ in found if v is not None]
    if len(known) < 2:
        findings.append("INSUFFICIENT: 금액이 2개 미만이라 교차 검증 불가.")
        return "insufficient", findings

    bad = False
    if sub is not None and vat is not None:
        exp = round_won(sub * VAT_RATE)
        if exp != vat:
            bad = True
            findings.append(f"MISMATCH: 부가세는 소계x0.10={exp} 이어야 하는데 {vat} 로 적혀 있다.")
    if sub is not None and tot is not None:
        exp = round_won(sub * (1 + VAT_RATE))
        if exp != tot:
            bad = True
            findings.append(f"MISMATCH: 합계는 소계x1.10={exp} 이어야 하는데 {tot} 로 적혀 있다.")
    if sub is None and vat is not None and tot is not None:
        exp_sub = round_won(tot / (1 + VAT_RATE))
        exp_vat = tot - exp_sub
        if exp_vat != vat:
            bad = True
            findings.append(
                f"MISMATCH: 합계 {tot} 역산 시 공급가 {exp_sub}, 세액 {exp_vat} 인데 {vat} 로 적혀 있다.")
    if sub is not None and vat is not None and tot is not None:
        if sub + vat != tot:
            bad = True
            findings.append(f"MISMATCH: 소계+부가세={sub + vat} 가 합계 {tot} 와 다르다.")

    return ("mismatch" if bad else "ok"), findings


SELF_TESTS = [
    ("소계 65,000원 부가세 6,500원 합계 71,500원", "ok"),
    ("소계 65,000원 부가세 3,250원 합계 68,250원", "mismatch"),  # 5% 오표기
    ("합계 55,000원 부가세 5,000원", "ok"),                      # 역산 50,000/5,000
    ("합계 55,000원 부가세 5,500원", "mismatch"),
    ("소계 33,333원 부가세 3,333원 합계 36,666원", "ok"),        # 반올림 경계
    ("면세 항목 소계 10,000원 부가세 0원", "skip"),
    ("총액 12,000원", "insufficient"),
]


def self_test():
    failed = 0
    for text, expect in SELF_TESTS:
        status, findings = check(text)
        mark = "PASS" if status == expect else "FAIL"
        if status != expect:
            failed += 1
        print(f"[{mark}] expect={expect} got={status} :: {text}")
        for f in findings:
            print(f"        {f}")
    print(f"\n self-test: {len(SELF_TESTS) - failed}/{len(SELF_TESTS)} 통과")
    return 0 if failed == 0 else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="한국 견적서 부가세 표기 점검 도구")
    ap.add_argument("--text", help="점검할 문자열")
    ap.add_argument("--file", help="점검할 텍스트 파일 경로")
    ap.add_argument("--self-test", action="store_true", help="내장 사례로 자체 검사")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    if args.file:
        try:
            data = open(args.file, encoding="utf-8").read()
        except OSError as e:
            print(f"파일을 읽을 수 없다: {e}", file=sys.stderr)
            return 2
    elif args.text:
        data = args.text
    else:
        ap.print_help()
        return 2

    status, findings = check(data)
    for f in findings:
        print(f)
    print(f"RESULT: {status}")
    return 1 if status == "mismatch" else 0


if __name__ == "__main__":
    sys.exit(main())
