# 한국어 MTP 드래프트 어휘사전 (NInfer · dgpp)

Qwen 계열 모델을 MTP 추측 디코딩(speculative decoding)으로 돌릴 때, **드래프트(초안) 단계가 쓰는 축소 어휘사전을 한국어에 맞게 다시 만들어** 한국어 생성 속도를 올린 작업 기록이다. 엔진 패치, 범용 어휘 생성 스크립트, 실측 결과를 담았다.

## 무엇을, 왜

- MTP 드래프트는 토큰을 하나 제안할 때마다 출력 헤드(lm_head, 약 24.8만 행)를 읽는다. 그래서 엔진들은 자주 쓰는 토큰만 남긴 **축소 드래프트 헤드**를 쓴다. 최종 확인(verify)은 전체 헤드로 하므로 **출력 분포는 바뀌지 않고**, 바뀌는 것은 드래프트 채택률과 읽기량뿐이다.
- 문제: 기본 축소 목록은 영어·중국어·코드·수학 말뭉치 빈도로 만들어져 있다.
  - **NInfer** `--lm-head-draft`의 기본 제안 목록(131,072개)은 한국어 텍스트 토큰을 **58~71%만** 덮는다. 나머지 한국어 토큰은 드래프트가 아예 제안할 수 없어서 한국어 MTP 채택률이 0.18~0.40에 머물렀다.
  - BPE 순서상 앞쪽 id(65,536개)를 쓰는 방식은 한국어 토큰의 45~49%만 덮었다.
- 해결: 한국어 도메인 말뭉치(매장 응대·견적 문체, 한국어 산문, 한국어 위키, 영어/코드)로 토큰 빈도를 세어 목록을 새로 만들었다. 65,536개로 한국어 토큰의 99.8~100%를 덮는다.
  - NInfer: 최종 목록 = **한국어 상위 65,536개 + 기존 목록 상위 65,536개 = 131,072개** (q4 커널이 이 행 수만 지원하므로 크기는 그대로 둠).
  - dgpp: 한국어 65,536개 목록을 `engine.draft_vocab`으로 사용.

## 결과

### NInfer — Qwen3.8-27B NVFP4 (Korean LoRA-merged), RTX 5090

500토큰 생성, temperature 0.7, 단일 요청, 3회 평균. 값 = tok/s / MTP 채택률. 서버 두 대(같은 RTX 5090 구성)에서 각각 측정했다.

| 프롬프트 | 서버 A 기존 | 서버 A 한국어 목록 | 서버 B 기존 | 서버 B 한국어 목록 |
|---|---|---|---|---|
| 한국어 매장 응대 | 91.3 / 0.18 | **112.5 / 0.31 (+23%)** | 98.7 / 0.18 | **125.4 / 0.30 (+27%)** |
| 한국어 설명 | 106.6 / 0.26 | **136.7 / 0.43 (+28%)** | 120.1 / 0.31 | **150.0 / 0.42 (+25%)** |
| 한국어 견적(숫자 많음) | 132.7 / 0.40 | **143.4 / 0.46 (+8%)** | 144.6 / 0.40 | **164.8 / 0.49 (+14%)** |
| 영어 | 145.3 / 0.47 | 142.8 / 0.46 | 153.6 / 0.44 | 154.2 / 0.44 |
| 코드 | 201.9 / 0.78 | 206.4 / 0.81 | 225.2 / 0.79 | 225.9 / 0.80 |

영어·코드는 기존 목록 상위 65,536개를 그대로 넣었기 때문에 변화가 측정 오차 범위 안이다. 도구 호출(tool call)과 그다음 턴도 정상 동작했다.

### dgpp — Qwen3.8-Flash-Next NVFP4, DGX Spark (GB10)

500토큰, temperature 0.7, thinking off, 단일 요청. 값 = tok/s / MTP 채택률.

| 프롬프트 | 기존(목록 없음) | 한국어 65,536 | 한국어 32,768 |
|---|---|---|---|
| 한국어 매장 응대 | 42.0 / 0.46 | **48.1 / 0.51** | 47.8 / 0.49 |
| 한국어 설명 | 48.6 / 0.61 | 49.0 / 0.59 | 53.0 / 0.60 |
| 한국어 견적 | 50.8 / 0.74 | **58.7 / 0.74** | 55.3 / 0.74 |
| 영어 | 47.4 / 0.63 | 50.1 / 0.59 | 50.7 / 0.59 |
| 코드 | 58.6 / 0.89 | 64.7 / 0.89 | 64.1 / 0.86 |

dgpp는 디코드 대략 +8~15%. 이 엔진은 드래프트 헤드 읽기량 자체가 줄어드는 효과(행 수 축소)가 주이고, 채택률 변화는 작다.

## 재현 방법

### 1) 어휘 목록 만들기 (`tools/build_draft_vocab.py`)

모델의 `tokenizer.json`과 직접 준비한 텍스트 폴더(.txt/.md/.json/.jsonl)를 넣으면 상위 N개 토큰 id를 `.npy`/`.txt`로 낸다. 특수 토큰과 바이트 토큰(0~255)은 항상 포함한다. 폴더마다 가중치를 줘서 큰 말뭉치(위키 등)가 도메인 텍스트를 덮어쓰지 않게 한다.

```bash
pip install tokenizers numpy

# 한국어 65,536개만 (dgpp engine.draft_vocab 용)
python tools/build_draft_vocab.py \
  --tokenizer tokenizer.json --tokenizer-config tokenizer_config.json \
  --corpus my_domain_ko:0.35 --corpus ko_prose:0.25 --corpus ko_wiki:0.15 --corpus en_code:0.25 \
  --top 65536 --out ko_draft_vocab_65536

# 기존 제안 목록과 합쳐 131,072개 (NInfer 용)
python tools/build_draft_vocab.py ... --top 65536 \
  --merge-with original_proposal_ids.npy --total 131072 --out ko65k_plus_orig_131072
```

`--merge-with`에는 기존 목록(순위순 id, .npy 또는 텍스트)을, `--merge-ranking`에는 NInfer의 토큰별 int64 빈도 파일을 넣을 수 있다. 기존 NInfer 목록은 변환된 artifact의 `proposal/token_ids`에서 꺼낼 수 있다.

> 우리가 실제로 쓴 어휘 파일은 비공개 매장 데이터에서 나온 것이라 공개하지 않는다. 각자 자기 도메인 텍스트로 만들면 된다.

### 2) NInfer (`patches/ninfer/`)

NInfer upstream 커밋 `d44ab58` 기준 패치 2개. **변환기(tools/convert)만 바뀌고 엔진(C++)과 이미지는 그대로**다. 테스트 포함.

```bash
git clone https://github.com/Neroued/ninfer && cd ninfer
git checkout d44ab58
git am /path/to/ninfer-korean-draft-vocab/patches/ninfer/*.patch

# 기존 변환 명령에 --proposal-ids 만 추가 (--proposal 자동 활성)
python -m tools.convert <기존 변환 인자들> \
  --proposal-ids ko65k_plus_orig_131072.npy \
  --out model_kodv.ninfer
```

- 서빙은 평소처럼 `--lm-head-draft`로 띄운다.
- **주의**: q4 제안 헤드 커널은 정해진 모양만 지원한다. hidden 5120 모델에서 65,536행 헤드는 기동 시 `q4 linear: unsupported shape`로 실패한다. 행 수를 **131,072로 맞출 것**(그래서 기존 목록과 합친다).
- 기존 artifact와 비교하면 `proposal/head`, `proposal/token_ids` 두 객체만 다르다.

### 3) dgpp (`patches/dgpp/`)

dgpp upstream 커밋 `24330a7` 기준 패치 1개. 원래 dgpp의 `engine.draft_vocab`(.npy)은 **AutoRound int8 헤드에서만** 동작하고, NVFP4 + `dense_weights: fp8` 헤드에서는 켜도 효과가 없었다. 이 패치는 fp8 헤드에서도 동작하게 한다: 목록에 든 BF16 행을 모아 block-128 FP8로 따로 인코딩하고, 드래프트 호출 때 조각 GEMM 후 나머지는 -inf로 채워 원래 id 위치에 scatter한다. `draft_vocab` 키가 없으면 예전과 똑같이 동작한다.

```bash
git clone https://github.com/HawkBearPig/dgpp && cd dgpp
git checkout 24330a7
git am /path/to/ninfer-korean-draft-vocab/patches/dgpp/*.patch
# 빌드 후 엔진 설정에 "draft_vocab": "ko_draft_vocab_65536.npy" 추가
```

## 주의사항

- 수치는 **단일 요청, 3회 측정**이다. 실제 서비스 중인 서버에서 쟀기 때문에 다른 요청이 끼어든 회차는 뺐지만 잡음이 남아 있다. 동시 요청 처리량은 따로 재지 않았다.
- 추측 디코딩은 무손실이다. 최종 토큰은 전체 헤드로 검증하고(샘플링은 분포 보존 거부 샘플링), 따라서 **출력 품질/분포는 바뀌지 않는다**. 바뀌는 것은 속도뿐이다. (dgpp는 원래부터 실행마다 greedy 출력이 조금씩 갈리는 비결정성이 있어서 출력 바이트 단위 비교는 하지 않았다.)
- 효과는 **한국어에만** 확인했다. 다른 언어도 같은 원리로 기대할 수 있지만 재 보지 않았다. 영어·코드는 변화가 없거나 오차 수준이다.
- 어휘 목록은 사용하는 모델의 토크나이저와 정확히 같은 것으로 만들어야 한다.

## 라이선스

- `patches/ninfer/` — [Neroued/ninfer](https://github.com/Neroued/ninfer)에 대한 패치. upstream과 같은 **Apache License 2.0**.
- `patches/dgpp/` — [HawkBearPig/dgpp](https://github.com/HawkBearPig/dgpp)에 대한 패치. upstream과 같은 **Apache License 2.0**.
- `tools/build_draft_vocab.py` — Apache License 2.0.
- 훌륭한 엔진을 공개해 준 NInfer(Neroued)와 dgpp(HawkBearPig) 개발자들께 감사드린다.

하이라이프PC (천안) — local AI setup

---

## English summary

**What**: a Korean draft (proposal) vocabulary for MTP speculative decoding, with patches for two inference engines and a generic builder script.

**Why**: the reduced draft heads ship with token lists ranked on English/Chinese/code/math text. NInfer's default 131,072-token proposal list covers only 58–71% of Korean text tokens, so Korean MTP acceptance stayed at 0.18–0.40. We counted token frequencies on a Korean-domain corpus; 65,536 ids then cover 99.8–100% of Korean tokens.

**Results** (500 tokens, temp 0.7, single request, 3 runs; tok/s / MTP acceptance):
- NInfer, Qwen3.8-27B NVFP4 (Korean LoRA-merged), RTX 5090, list = 65,536 Korean + top 65,536 of the original = 131,072 rows: Korean store reply +23–27%, Korean explanation +25–28%, Korean quote +8–14%; English and code unchanged (within noise). Acceptance e.g. 0.18 → 0.30–0.31, 0.26–0.31 → 0.42–0.43.
- dgpp, Qwen3.8-Flash-Next NVFP4, DGX Spark (GB10), 65,536 Korean ids: decode roughly +8–15% (Korean store reply 42.0 → 48.1, quote 50.8 → 58.7, code 58.6 → 64.7 tok/s).

**Contents**
- `patches/ninfer/` — 2 patches on upstream `d44ab58`: `tools/convert --proposal-ids FILE` (.npy or text) selects the proposal rows directly; converter-only, with tests. Keep 131,072 rows (q4 kernel shape constraint for hidden 5120).
- `patches/dgpp/` — 1 patch on upstream `24330a7`: makes `engine.draft_vocab` work with the `dense_weights: fp8` LM head (previously int8 AutoRound head only).
- `tools/build_draft_vocab.py` — tokenizer + folders of your own text (weighted groups) → top-N ids (.npy/.txt), optional merge with an existing proposal list to a fixed total.

**Caveats**: single-request numbers, 3 runs, measured on live servers (runs with concurrent traffic dropped, some noise remains). Speculative decoding is lossless — outputs/distribution are unchanged, only speed. Verified for Korean only. Our own vocabulary files are not published (derived from private data).

**License**: patches are Apache-2.0 per upstream; thanks to [Neroued/ninfer](https://github.com/Neroued/ninfer) and [HawkBearPig/dgpp](https://github.com/HawkBearPig/dgpp). Builder script Apache-2.0.

HighLife PC (Cheonan, Korea) — local AI setup
