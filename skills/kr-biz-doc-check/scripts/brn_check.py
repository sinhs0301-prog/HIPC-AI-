#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""brn_check.py - 한국 사업자등록번호(10자리) 체크섬 자가검증 도구.

목적
  견적서/계산서/거래처 명부에 적힌 사업자등록번호가 '형식상 유효한 번호인지'를
  네트워크 없이 오프라인에서 확인한다. 오타(자리 바꿈, 한 자리 오입력)를
  대부분 잡아낸다.

한계 (반드시 읽을 것)
  - 이 도구는 체크섬 규칙만 검사한다. 실제로 국세청에 등록된 사업자인지,
    휴폐업 상태인지는 알 수 없다. 그 확인은 국세청 홈택스/공공데이터포털
    사업자등록정보 진위확인 API 같은 공식 경로가 필요하다.
  - 따라서 '유효'는 '형식상 성립'이라는 뜻이며 실재 보증이 아니다.

검증 규칙 (널리 공개된 표준 체크섬)
  번호 10자리를 d1..d10이라 할 때 가중치 w = [1,3,7,1,3,7,1,3,5]
    s = sum(d_i * w_i for i in 1..9)
    s += (d9 * 5) // 10
    check = (10 - (s % 10)) % 10
  check == d10 이면 형식상 유효.

사용법
  python brn_check.py --number 000-00-00000
  python brn_check.py --file numbers.txt
  python brn_check.py --selftest
  python brn_check.py --fix 123-45-6789     (앞 9자리로 올바른 검증번호 계산)

MIT 라이선스. 작성: 클로드(1번 전용), 헤르메스 실험1 팀.
"""
import argparse
import re
import sys

WEIGHTS = [1, 3, 7, 1, 3, 7, 1, 3, 5]


def normalize(raw):
    """입력에서 숫자만 뽑아낸다. 하이픈/공백/괄호는 무시한다."""
    return re.sub(r"\D", "", raw or "")


def check_digit(first9):
    """앞 9자리(문자열)로 10번째 검증숫자를 계산한다."""
    if len(first9) != 9 or not first9.isdigit():
        raise ValueError("앞 9자리 숫자가 필요합니다.")
    digits = [int(c) for c in first9]
    total = sum(d * w for d, w in zip(digits, WEIGHTS))
    total += (digits[8] * 5) // 10
    return (10 - (total % 10)) % 10


def validate(raw):
    """검증 결과를 dict로 돌려준다. 예외를 던지지 않는다."""
    digits = normalize(raw)
    out = {
        "input": raw,
        "digits": digits,
        "valid": False,
        "reason": "",
        "expected_check": None,
        "formatted": None,
    }
    if not digits:
        out["reason"] = "숫자가 없습니다."
        return out
    if len(digits) != 10:
        out["reason"] = "숫자가 %d개입니다. 사업자등록번호는 10자리여야 합니다." % len(digits)
        return out
    expected = check_digit(digits[:9])
    out["expected_check"] = expected
    out["formatted"] = "%s-%s-%s" % (digits[:3], digits[3:5], digits[5:])
    if expected == int(digits[9]):
        out["valid"] = True
        out["reason"] = "체크섬 일치(형식상 유효). 실제 등록/휴폐업 여부는 확인하지 않음."
    else:
        out["reason"] = "체크섬 불일치: 마지막 자리가 %s인데 규칙상 %d이어야 합니다." % (digits[9], expected)
    return out


def _selftest():
    """규칙 자체의 일관성과 오타 검출력을 확인한다.

    주의: 여기 쓰는 번호는 실재 사업자가 아니라 규칙으로 만든 시험값이다.
    """
    failures = []

    # 1) 앞 9자리 여러 개로 검증숫자를 만들고 다시 검증하면 항상 유효해야 한다.
    seeds = ["123456789", "000000000", "999999999", "104811234", "220881050", "305820001"]
    built = []
    for s in seeds:
        full = s + str(check_digit(s))
        built.append(full)
        r = validate(full)
        if not r["valid"]:
            failures.append("생성한 번호 %s 가 유효하지 않다: %s" % (full, r["reason"]))

    # 2) 한 자리 오타는 반드시 걸러져야 한다(단일 자리 변경 전수 검사).
    missed = 0
    total_mutations = 0
    for full in built:
        for i in range(10):
            for d in "0123456789":
                if d == full[i]:
                    continue
                total_mutations += 1
                bad = full[:i] + d + full[i + 1:]
                if validate(bad)["valid"]:
                    missed += 1
    if total_mutations == 0:
        failures.append("변형 시험이 수행되지 않았다.")
    detect_rate = 0.0 if total_mutations == 0 else (total_mutations - missed) / total_mutations

    # 3) 형식 정규화: 하이픈/공백이 있어도 같은 결과여야 한다.
    sample = built[0]
    pretty = "%s-%s-%s" % (sample[:3], sample[3:5], sample[5:])
    if validate(pretty)["valid"] != validate(sample)["valid"]:
        failures.append("하이픈 표기와 숫자 표기의 결과가 다르다.")
    if validate(" " + pretty + " ")["valid"] is not True:
        failures.append("앞뒤 공백 처리 실패.")

    # 4) 잘못된 길이는 유효로 판정하면 안 된다.
    for bad in ["12345", "12345678901", "", "abc"]:
        if validate(bad)["valid"]:
            failures.append("길이/형식 오류 입력 %r 을 유효로 판정했다." % bad)

    print("[selftest] 생성 검증 번호 %d건" % len(built))
    for b in built:
        print("  생성: %s-%s-%s" % (b[:3], b[3:5], b[5:]))
    print("[selftest] 단일자리 오타 %d건 중 검출 %d건 (검출률 %.4f)"
          % (total_mutations, total_mutations - missed, detect_rate))
    print("[selftest] 미검출(체크섬을 통과한 오타) %d건" % missed)
    if failures:
        print("[selftest] 실패 %d건:" % len(failures))
        for f in failures:
            print("  - " + f)
        return 1
    print("[selftest] 통과: 규칙 일관성/정규화/길이검사 이상 없음")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(
        description="한국 사업자등록번호 10자리 체크섬 자가검증(오프라인). 실제 등록 여부는 확인하지 않습니다."
    )
    p.add_argument("--number", "-n", action="append", default=[],
                   help="검사할 번호. 여러 번 쓸 수 있음. 하이픈 허용.")
    p.add_argument("--file", "-f", help="한 줄에 하나씩 번호가 적힌 텍스트 파일")
    p.add_argument("--fix", help="앞 9자리를 주면 올바른 마지막 검증숫자를 계산")
    p.add_argument("--selftest", action="store_true", help="내장 시험 실행")
    args = p.parse_args(argv)

    if args.selftest:
        return _selftest()

    if args.fix:
        d = normalize(args.fix)
        if len(d) < 9:
            print("앞 9자리 숫자가 필요합니다. 입력 숫자 %d개." % len(d))
            return 2
        d9 = d[:9]
        c = check_digit(d9)
        print("%s-%s-%s%d" % (d9[:3], d9[3:5], d9[5:], c))
        return 0

    targets = list(args.number)
    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        targets.append(line)
        except OSError as e:
            print("파일을 열 수 없습니다: %s" % e)
            return 2

    if not targets:
        p.print_help()
        return 2

    bad = 0
    for t in targets:
        r = validate(t)
        mark = "유효" if r["valid"] else "오류"
        shown = r["formatted"] or r["digits"] or t
        print("[%s] %s : %s" % (mark, shown, r["reason"]))
        if not r["valid"]:
            bad += 1
    print("---")
    print("검사 %d건, 형식상 유효 %d건, 오류 %d건" % (len(targets), len(targets) - bad, bad))
    print("주의: 체크섬만 본 결과이며 실제 등록/휴폐업 여부는 국세청 공식 조회가 필요합니다.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
