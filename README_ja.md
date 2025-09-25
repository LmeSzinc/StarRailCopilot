**| [English](README_en.md) | [简体中文](README.md) | [Español](README_es.md) | 日本語 |**


# StarRailCopilot

Star Rail 自動スクリプト | 崩壊：スターレイル自動化スクリプト、次世代Alasフレームワークベース。

![gui](https://raw.githubusercontent.com/wiki/LmeSzinc/StarRailCopilot/README.assets/gui_cn.png)

![setting](https://raw.githubusercontent.com/wiki/LmeSzinc/StarRailCopilot/README.assets/setting_cn.png)

## 機能

- **ダンジョン攻略**：[キャラクター育成計画](https://github.com/LmeSzinc/StarRailCopilot/wiki/Planner_cn)、デイリーダンジョン、ダブルイベントダンジョン、歴戦流転。
- **収集**：デイリークエスト完了、委託派遣の回収、無名勲礼報酬の受け取り。
- **模擬宇宙**：模擬宇宙の周回、開拓力を使用した内周遺物収集。
- **バックグラウンド管理**：エミュレーターとゲームの自動起動、スタミナ消費とデイリーのバックグラウンド管理、ダッシュボードでリソース状況を把握。
- **クラウドゲーム**：（中国版のみ）[クラウド崩壊スターレイルでSRCを実行](https://github.com/LmeSzinc/StarRailCopilot/wiki/Cloud_cn)

## インストール [![](https://img.shields.io/github/downloads/LmeSzinc/StarRailCopilot/total?color=4e4c97)](https://github.com/LmeSzinc/StarRailCopilot/releases)

[中国語インストールガイド](https://github.com/LmeSzinc/StarRailCopilot/wiki/Installation_cn)、自動インストールチュートリアル、使用方法、手動インストールチュートリアルを含む。

[デバイスサポートドキュメント](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/Emulator_cn)、Windows/Mac/Linuxおよび様々な実行方法をサポート。

> **なぜエミュレーターを使用するのか？** デスクトップ版でスクリプトを実行する場合、ゲームウィンドウを前面に保つ必要があります。スクリプト実行中にマウスやキーボードが使えないのは不便でしょう。そのためエミュレーターを使用します。

> **エミュレーターのパフォーマンスは？** Lmeの8700k+1080tiでMuMu 12エミュレーターを使用し、画質設定を非常に高くしても40fpsが出ます。もう少し新しい構成なら、最高エフェクトで60fpsも問題ありません。

## 開発

QQグループ1 752620927 (開発希望者はグループ1へ)
QQグループ2 1033583803
Discord https://discord.gg/aJkt3mKDEr

- [ミニマップ認識原理](https://github.com/LmeSzinc/StarRailCopilot/wiki/MinimapTracking)
- 開発ドキュメント（サイドバーに目次）：[Alas wiki](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/1.-Start)、ただし多くの内容は新しく書かれているため、ソースコードと履歴コミットの参照を推奨。
- 開発ロードマップ：ピン留めされたissueを参照。PRの提出を歓迎します。興味のある部分を選んで開発してください。

> **多言語/多サーバーサポートを追加するには？** assetsの適応が必要です。[開発ドキュメント「Buttonの追加」セクション](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/4.1.-Detection-objects#%E6%B7%BB%E5%8A%A0%E4%B8%80%E4%B8%AA-button)を参照してください。

## Alasについて

SRCはアズールレーンスクリプト[AzurLaneAutoScript](https://github.com/LmeSzinc/AzurLaneAutoScript)をベースに開発されています。Alasは3年の開発を経て高い完成度に達していますが、技術的負債も蓄積されており、新プロジェクトでこれらの問題を解決したいと考えています。

- OCRライブラリの更新。Alasはcnocr==1.2.2で複数のモデルを訓練しましたが、依存している[mxnet](https://github.com/apache/mxnet)はあまり活発ではありません。機械学習の急速な発展により、新しいモデルは速度と精度の両面で旧モデルを圧倒しています。
- 設定ファイルの[pydantic](https://github.com/pydantic/pydantic)化。サブタスクとスケジューラーの概念が導入されて以来、ユーザー設定の数が倍増しました。Alasは独自のコードジェネレーターを作成して設定ファイルの更新とアクセスを処理していますが、pydanticによりこの部分がより簡潔になります。
- より良いAssets管理。button_extractはAlasが4000以上のテンプレート画像を簡単に維持するのに役立ちましたが、深刻なパフォーマンスの問題があり、海外版の不足しているAssetsに関する通知も大量のゴミログに埋もれています。
- アズールレーンへの結合度の削減。AlasフレームワークとAlas GUIには他のゲームやスクリプトと連携する能力がありますが、完成したアークナイツ[MAA](https://github.com/MaaAssistantArknights/MaaAssistantArknights)プラグインと開発中の[fgo-py](https://github.com/hgjazhgj/FGO-py)プラグインは、Alasとアズールレーンゲーム自体の結合度が高いという問題を発見しました。
