# CUHK-X Multimodal Human Activity Challenge

**Official website:** https://openaiotlab.github.io/CUHK-X-Challenge/

An international competition on **privacy-preserving** human activity understanding, hosted by the
[AIoT Lab](https://github.com/openaiotlab) at The Chinese University of Hong Kong and co-located with
**UbiComp 2026** (Shanghai). RGB data is excluded entirely — models learn human dynamics from
**depth, IMU, mmWave radar, skeleton, thermal, and infrared** modalities.

| | |
|---|---|
| **Tracks** | 2 parallel Kaggle competitions |
| **Modalities** | Depth · IMU · mmWave · Skeleton · Thermal · Infrared (no RGB) |
| **Action classes** | 40 daily activities |
| **Duration** | June 20 – September 15, 2026 |
| **Finals** | UbiComp 2026 · Shanghai · Oct 11, 2026 |
| **Prize pool** | USD $20,000 ($10,000 per track) |

## Tracks

### Small Model Track — HAR (lightweight)
40-class cross-subject human activity recognition for resource-constrained edge deployment.
CNN / RNN / Transformer architectures, **model size ≤ 100 MB**, no large pretrained backbones.

→ https://www.kaggle.com/competitions/cuhk-x-competition-small-model-track

### Large Model Track — VQA (HAU & HARn)
Human Action Understanding and Human Action Reasoning via visual question answering on
privacy-preserving video. No parameter limit; LVLMs, closed-source APIs, and prompt engineering
are encouraged.

→ https://www.kaggle.com/competitions/cuhk-x-competition-large-model-track

Both tracks use the same cross-subject split — train: users 1–9 & 16–24, public test: users 10–11 & 25–26,
private test: held out.

## Competition format

1. **Kaggle open competition** (Jun 20 – Sep 15, 2026) — private leaderboard decides ranking; top 15 teams per track advance.
2. **Selection stage** (Sep 16 – 30, 2026) — Zoom verification with live inference on freshly released sample data plus offline reproduction of Kaggle results; top 6 teams per track advance.
3. **UbiComp finals** (Oct 11, 2026, Shanghai) — on-site inference on a brand-new private dataset, 15-min technical report and Q&A, awards ceremony. Up to USD $500 travel grant per attending finalist team; remote participation via Zoom is supported.

Finalist scoring: Kaggle private LB 20% · on-site private test 30% · reproducibility 10% ·
technical report 20% · presentation 10% · model efficiency 10%.

## Awards

Per track: 1st $6,000 · 2nd $3,000 · 3rd $1,000, plus Best Report, Most Popular, and Best Faculty
Advisor awards. All participants are recognized through a 5-tier certificate system (Outstanding,
Finalist, Excellence, Distinction, Successful Participation).

## Dataset

**CUHK-X** contains 64,267 fully synchronized samples from 30 participants performing 40 daily
activities across two real-world indoor environments, with seven modalities
(RGB, depth, thermal, infrared, skeleton, IMU ×5, mmWave radar). The challenge uses everything
except RGB. Annotations follow a Ground-Truth First strategy combining LLM-generated scene
descriptions with human review, supporting three progressive tasks: HAR, HAU, and HARn.

- Dataset homepage: https://openaiotlab.github.io/CUHK-X/
- Code & docs: https://github.com/openaiotlab/CUHK-X
- Downloads — Small Model Track: [Hugging Face](https://huggingface.co/datasets/Kevin-Pal/CUHK-X_Small_Model_Track) · [Google Drive](https://drive.google.com/drive/folders/1wZOPpTFLqDKjBLJGjMdOZyuJygLHbwCZ?usp=sharing) · [Baidu Netdisk](https://pan.baidu.com/s/1uvaN88D8oHKkaa5O_b4x5g?pwd=5855)
- Downloads — Large Model Track: [Hugging Face](https://huggingface.co/datasets/Kevin-Pal/CUHK-X_Large_Model_Track) · [Google Drive](https://drive.google.com/drive/folders/1USLiJKosAyA7oSuxU27d-s_lxJyKKjya?usp=sharing) · [Baidu Netdisk](https://pan.baidu.com/s/10uVVQiWr5gXiiReXQxUkdQ?pwd=huxi)

## Registration

1. Register your team on the [official website](https://openaiotlab.github.io/CUHK-X-Challenge/#registration) — required for prizes, announcements, and finals invitations.
2. Join the Kaggle competition and create your team there with the **exact same team name**.

Teams are 1–3 members (faculty advisor not counted); each individual may join only one team per
track, but participation in both tracks is allowed.

## This repository

This repo hosts the challenge website (GitHub Pages) and its supporting scripts.

```
index.html                          # the full single-page website
leaderboard.json                    # top-6 per track, auto-synced from Kaggle
photos/                             # organizer portraits
Rule/
  IP_CLAUSES_BILINGUAL.pdf          # IP clauses and competition terms (EN/中文)
  LICENSE.txt                       # dataset license and terms
scripts/
  update_leaderboard.py             # fetches Kaggle leaderboards → leaderboard.json
  make_ip_pdf.py                    # generates the bilingual IP clauses PDF
.github/workflows/
  update-leaderboard.yml            # daily at 02:00 UTC (10:00 HKT) + manual dispatch
```

The leaderboard workflow needs the `KAGGLE_USERNAME` and `KAGGLE_KEY` repository secrets.

## Organizers

**Competition Co-Chairs:** Prof. Zhenyu Yan · Prof. Hongkai Chen · Siyang Jiang
**Competition Committee:** Guangyu Chen · Liekang Zeng · Anlan Peng · Xiang Ji · Mu Yuan
**Steering Committee:** Prof. Guoliang Xing

All CUHK · AIoT Lab, Dept. of Information Engineering.

## Contact

General inquiries: **cuhkx.competition@gmail.com**
