# Yusuke Mukaiyama

バックエンドエンジニアとして、Web サービスのサーバーサイド開発に携わっています。
あわせて、クラウド基盤（AWS）の設計力を体系的に積み上げているところです。

「動けばいい」で止めず、壊れ方まで設計することを大事にしています。

---

## バックエンド

Ruby / Ruby on Rails でのサーバーサイド開発が主戦場です。API と、大量のデータを扱う定期実行処理の設計・実装を経験しています。

設計で意識していること:

- **fail-fast なエラー設計** — 不正な入力や設定不足を握り潰さず、異常はその場で落として原因を特定できる状態にする
- **メモリ効率を意識したデータ処理** — 全件をメモリに載せず遅延評価で流し、データ量の増加に耐える構造にする
- **レイヤ分離とテスト** — 取得・変換・出力の責務を分け、各層を単体で検証できる形に保つ

## クラウド / AWS

AWS 認定資格の取得に向けて、ハンズオン中心で体系的に学習しています（SAA-C03 → DVA → SAP-C02 → DOP の順に取得予定）。

手を動かして学んでいる範囲:

- **ネットワーク** — VPC / サブネット設計、セキュリティグループと NACL、NAT Gateway、VPC エンドポイント
- **可用性・回復性** — マルチ AZ 構成、ELB + Auto Scaling、RDS のフェイルオーバー、バックアップとリストア設計
- **サーバーレス** — Lambda / API Gateway / DynamoDB / S3 / EventBridge
- **セキュリティ** — IAM のポリシー設計と最小権限、KMS による暗号化、Secrets Manager
- **IaC・コスト最適化** — CloudFormation によるスタック管理、ストレージクラスと料金体系を踏まえた構成選択

## 技術スタック

| 領域 | 主に使うもの |
| --- | --- |
| 言語 | Ruby / TypeScript / Python |
| バックエンド | Ruby on Rails, RSpec |
| クラウド | AWS（学習中）, Cloudflare (Workers / D1 / R2), Supabase |
| フロントエンド | Astro |
| その他 | Git / GitHub Actions, Docker, Google Apps Script |

## 個人開発

身のまわりの定型作業を自動化するツールと、Web サイトを個人でつくって運用しています。

- **自動化** — LINE Messaging API / Python / Google Apps Script で、料金明細の取得・空き枠監視・レポート生成などを定期実行の形で運用中
- **Web サイト制作** — Astro + Cloudflare で [ouen-hp.jp](https://ouen-hp.jp/) ほか計4サイトを公開・運用。本番反映前に Lighthouse とビジュアル回帰テストを自動で通す仕組みを整備し、案件をまたいで同じ品質基準で回しています

## お問い合わせ

[ouen-hp.jp](https://ouen-hp.jp/)
