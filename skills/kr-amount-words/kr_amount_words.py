#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kr_amount_words.py - 한국 원화 금액의 한글 표기 변환/역변환 (표준 라이브러리만 사용)

용도:
  견적서, 계약서, 세금계산서, 지출결의서 등에서 쓰는
  '일금 삼백이십일만오천원정' 형식의 한글 금액 표기를 만들고,
  반대로 한글 표기를 숫자로 되돌려 사람이 적은 값을 검산한다.

표기 규칙(중요):
  - 만 단위 그룹에서는 선행 1을 생략한다. 예: 10000 -> '만', 10001 -> '만일'
  - 억/조/경 단위 그룹에서는 선행 1을 항상 적는다.
    예: 100000000 -> '일억', 120000000 -> '일억이천만', 10**12 -> '일조',
        10**18 -> '일백경' (억 이상 그룹은 백/천 자리의 1도 적는다)
  - explicit_one=True로 부르면 모든 그룹에서 1을 적는다. 예: 1200 -> '일천이백'
  - 역변환(korean_to_num)은 '억'과 '일억', '백경'과 '일백경'을 모두 해석한다.

한계:
  - 0 이상의 정수 원화만 다룬다. 소수점(전 단위)은 지원하지 않는다.
  - 지원 범위는 0 이상 10^20 미만(경 단위까지)이다.
  - 법적 효력이나 특정 기관 양식 통과를 보증하지 않는다. 최종 확인은 사용자 책임이다.

idea_key: kr won amount to korean words
License: MIT (본 파일 저작자 직접 작성)
"""

import random
import sys

DIGITS = "영일이삼사오육칠팔구"
SMALL = ["", "십", "백", "천"]
BIG = ["", "만", "억", "조", "경"]
MAX_VALUE = 10 ** 20  # 경 단위 4자리까지


def _four_to_korean(value, explicit_one):
    """0..9999 정수를 한글로. explicit_one=True면 '일천이백'처럼 1을 항상 적는다."""
    out = []
    for i, place in enumerate((1000, 100, 10, 1)):
        d = (value // place) % 10
        if d == 0:
            continue
        pos = 3 - i
        if d == 1 and pos > 0 and not explicit_one:
            out.append(SMALL[pos])
        else:
            out.append(DIGITS[d] + SMALL[pos])
    return "".join(out)


def num_to_korean(n, explicit_one=False):
    """정수 -> 한글 수 표기. 예: 3215000 -> '삼백이십일만오천'

    억(gi>=2) 이상 그룹은 선행 1을 생략하지 않는다(금액 표기 관례).
    """
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("정수만 지원합니다")
    if n < 0:
        raise ValueError("0 이상의 금액만 지원합니다")
    if n >= MAX_VALUE:
        raise ValueError("지원 범위(10^20 미만)를 넘었습니다")
    if n == 0:
        return "영"

    groups = []
    idx = 0
    rest = n
    while rest > 0:
        groups.append((rest % 10000, idx))
        rest //= 10000
        idx += 1

    parts = []
    for value, gi in reversed(groups):
        if value == 0:
            continue
        # 억 이상 그룹은 1을 항상 표기해 '백경'/'일백경' 혼선을 없앤다.
        group_explicit = explicit_one or gi >= 2
        if value == 1 and gi > 0 and not group_explicit:
            chunk = ""
        else:
            chunk = _four_to_korean(value, group_explicit)
        parts.append(chunk + BIG[gi])
    return "".join(parts)


def format_amount(n, style="formal", explicit_one=False):
    """style: formal -> '일금 삼백만원정', plain -> '삼백만원', bare -> '삼백만'"""
    words = num_to_korean(n, explicit_one=explicit_one)
    if style == "formal":
        return "일금 " + words + "원정"
    if style == "plain":
        return words + "원"
    if style == "bare":
        return words
    raise ValueError("style은 formal/plain/bare 중 하나여야 합니다")


def korean_to_num(text):
    """한글 금액 표기 -> 정수. '일금', '원', '원정', 공백, 쉼표를 허용한다."""
    if not isinstance(text, str):
        raise TypeError("문자열만 지원합니다")
    s = text.strip().replace(" ", "").replace(",", "")
    if s.startswith("일금"):
        s = s[2:]
    if s.endswith("원정"):
        s = s[:-2]
    elif s.endswith("원"):
        s = s[:-1]
    if s == "":
        raise ValueError("빈 표기입니다")
    if s == "영":
        return 0

    total = 0
    cur = 0
    num = 0
    for ch in s:
        if ch in DIGITS[1:]:
            num = DIGITS.index(ch)
        elif ch in SMALL[1:]:
            unit = 10 ** SMALL.index(ch)
            cur += (num if num else 1) * unit
            num = 0
        elif ch in BIG[1:]:
            big = 10 ** (4 * BIG.index(ch))
            cur += num
            num = 0
            total += (cur if cur else 1) * big
            cur = 0
        else:
            raise ValueError("해석할 수 없는 글자: %r" % ch)
    return total + cur + num


def verify(n, text):
    """숫자와 사람이 적은 한글 표기가 일치하는지 검산한다."""
    parsed = korean_to_num(text)
    return {
        "amount": n,
        "given_text": text,
        "parsed": parsed,
        "match": parsed == n,
        "expected_text": format_amount(n),
    }


def _selftest():
    fails = []
    checked = 0

    fixed = {
        0: "영",
        1: "일",
        10: "십",
        11: "십일",
        100: "백",
        1000: "천",
        10000: "만",
        10001: "만일",
        100000: "십만",
        3215000: "삼백이십일만오천",
        100000000: "일억",
        120000000: "일억이천만",
        1000000000000: "일조",
        1000000000000000000: "일백경",
    }
    for n, expect in fixed.items():
        got = num_to_korean(n)
        checked += 1
        if got != expect:
            fails.append("고정값 %d: 기대 %s / 실제 %s" % (n, expect, got))

    # 억 이상 선행 1 표기 확인 (생략되면 실패)
    for n in (10 ** 8, 10 ** 12, 10 ** 16, 10 ** 18, 10 ** 9):
        checked += 1
        if not num_to_korean(n).startswith("일"):
            fails.append("억 이상 선행 1 누락: %d -> %s" % (n, num_to_korean(n)))

    # 만 단위는 선행 1 생략 유지
    for n, expect in ((10000, "만"), (10000 + 1, "만일"), (12000, "만이천")):
        checked += 1
        if num_to_korean(n) != expect:
            fails.append("만 단위 표기 불일치 %d -> %s" % (n, num_to_korean(n)))

    # 왕복 검사 1: 0~30000 전수
    for n in range(0, 30001):
        checked += 1
        if korean_to_num(num_to_korean(n)) != n:
            fails.append("왕복(소액) 실패 n=%d -> %s" % (n, num_to_korean(n)))

    # 왕복 검사 2: 난수 대액 20000건 (형식 3종 x explicit_one 2종)
    rnd = random.Random(20260921)
    for _ in range(20000):
        n = rnd.randrange(0, MAX_VALUE)
        for eo in (False, True):
            for style in ("formal", "plain", "bare"):
                checked += 1
                text = format_amount(n, style=style, explicit_one=eo)
                if korean_to_num(text) != n:
                    fails.append("왕복(대액) 실패 n=%d style=%s eo=%s -> %s" % (n, style, eo, text))

    # 경계값 왕복 검사
    for n in (10 ** 4, 10 ** 4 + 1, 10 ** 8, 10 ** 8 + 1, 10 ** 12, 10 ** 16, 10 ** 18, MAX_VALUE - 1):
        checked += 1
        if korean_to_num(num_to_korean(n)) != n:
            fails.append("경계값 왕복 실패 n=%d -> %s" % (n, num_to_korean(n)))

    # '억'처럼 선행 1을 생략한 사람 입력도 해석되는지
    legacy = {"억": 10 ** 8, "조": 10 ** 12, "억이천만": 120000000, "백경": 10 ** 18}
    for text, expect in legacy.items():
        checked += 1
        if korean_to_num(text) != expect:
            fails.append("구표기 해석 실패 %s -> %d" % (text, korean_to_num(text)))

    # 오류 처리 검사
    bad_inputs = ["삼백X만", "", "  "]
    for bad in bad_inputs:
        checked += 1
        try:
            korean_to_num(bad)
            fails.append("잘못된 입력인데 통과함: %r" % bad)
        except ValueError:
            pass
    for bad_n in (-1, MAX_VALUE):
        checked += 1
        try:
            num_to_korean(bad_n)
            fails.append("범위를 벗어난 값인데 통과함: %d" % bad_n)
        except ValueError:
            pass

    print("[자체검사] 총 검사 %d건, 실패 %d건" % (checked, len(fails)))
    for f in fails[:20]:
        print("  - " + f)
    return 0 if not fails else 1


def _usage():
    print("사용법:")
    print("  python kr_amount_words.py --selftest")
    print("  python kr_amount_words.py 3215000            # 숫자 -> 한글")
    print("  python kr_amount_words.py '일금 삼백만원정'   # 한글 -> 숫자")
    print("  python kr_amount_words.py --verify 3000000 '일금 삼백만원정'")


def main(argv):
    if len(argv) < 2:
        _usage()
        return 2
    if argv[1] == "--selftest":
        return _selftest()
    if argv[1] in ("-h", "--help"):
        _usage()
        return 0
    if argv[1] == "--verify":
        if len(argv) < 4:
            _usage()
            return 2
        result = verify(int(argv[2].replace(",", "")), argv[3])
        print("금액: %d" % result["amount"])
        print("입력 표기: %s" % result["given_text"])
        print("해석 결과: %d" % result["parsed"])
        print("일치 여부: %s" % ("일치" if result["match"] else "불일치"))
        print("권장 표기: %s" % result["expected_text"])
        return 0 if result["match"] else 1

    arg = argv[1].strip()
    plain = arg.replace(",", "")
    if plain.isdigit():
        n = int(plain)
        print("정식: %s" % format_amount(n, "formal"))
        print("일반: %s" % format_amount(n, "plain"))
        print("1 표기: %s" % format_amount(n, "formal", explicit_one=True))
        print("숫자: {:,}원".format(n))
        return 0
    try:
        n = korean_to_num(arg)
    except ValueError as e:
        print("해석 실패: %s" % e)
        return 1
    print("숫자: {:,}원".format(n))
    print("권장 표기: %s" % format_amount(n))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
