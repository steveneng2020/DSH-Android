#!/usr/bin/env python3
"""为 fork 的 v0.2.2 基座重建生成 10 种语言的更新记录源文件。

上游 v0.2.2 要求 `docs/releases/build{code}-changes.{locale}.md` 共 10 个 locale，
首行必须严格等于 `# DSHA {versionName} / build{code}`，正文非空且不超过 16 KiB，
否则 `tools/generate-changelog.py --check` 会在 preBuild 阶段直接失败。

本脚本一次生成 10 份，正文内容按语言给出等价说明；翻译只覆盖本轮实际改动，
不做机翻堆砌。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ['zh', 'zh-Hant', 'en', 'ru', 'ja', 'ko', 'ar', 'pt', 'la', 'fr']

BODY = {
    'zh': """本版以 DSHA 上游 0.2.2（build357）为新基座重建，内置 DSH 0.2.2-rc.1，Ubuntu 基础环境仍为 10。

- 基座升级：从上游 0.2.1-rc.2（build190）整体升级到 0.2.2（build357），含移动界面 v5、设备能力授权页独立成页、维护期插件注册死锁修复。
- 单变体：移除兼容线与 GeckoView，只发布 Standard（Android 11 及以上、arm64-v8a、系统 WebView）。
- 保留本 fork 的自有功能：应用图标可点击切换六套配色、更新日记面板、上游对比、推理档位自动适配、插件原生依赖体检。
- 发行身份保持独立：包名 `dsh.android.dev`、自有发布证书，与上游 `dsh.android.client` 互不通用，覆盖安装需同签名。
- 更新源仍指向本仓库的 `updates.json`，APK 由本仓库 Releases 提供。

本版 `versionCode` 为 `20050357`。已安装旧版的用户点“检查更新”不会看到此版本（更新器要求 versionCode 更大），需手动下载覆盖安装。
实际软件检查与设备验收范围以本轮交付回执为准，不代表完整设备矩阵已验证。""",
    'zh-Hant': """本版以 DSHA 上游 0.2.2（build357）為新基座重建，內建 DSH 0.2.2-rc.1，Ubuntu 基礎環境仍為 10。

- 基座升級：從上游 0.2.1-rc.2（build190）整體升級到 0.2.2（build357），含行動介面 v5、裝置能力授權頁獨立成頁、維護期外掛註冊死鎖修復。
- 單一變體：移除相容線與 GeckoView，只發佈 Standard（Android 11 以上、arm64-v8a、系統 WebView）。
- 保留本 fork 的自有功能：應用圖示可點擊切換六套配色、更新日記面板、上游對比、推理檔位自動適配、外掛原生依賴體檢。
- 發行身分保持獨立：套件名 `dsh.android.dev`、自有發佈憑證，與上游 `dsh.android.client` 互不通用，覆蓋安裝需同簽章。
- 更新來源仍指向本儲存庫的 `updates.json`，APK 由本儲存庫 Releases 提供。

本版 `versionCode` 為 `20050357`。已安裝舊版的用戶點「檢查更新」不會看到此版本（更新器要求 versionCode 更大），需手動下載覆蓋安裝。
實際軟體檢查與裝置驗收範圍以本輪交付回執為準，不代表完整裝置矩陣已驗證。""",
    'en': """This build is rebuilt on the DSHA upstream 0.2.2 (build357) base, bundling DSH 0.2.2-rc.1; the Ubuntu base environment remains 10.

- Base upgrade: from upstream 0.2.1-rc.2 (build190) to 0.2.2 (build357), including mobile UI v5, a standalone device-capability authorisation page, and the maintenance-time plugin registration deadlock fix.
- Single variant: the compatibility line and GeckoView are removed; only Standard ships (Android 11+, arm64-v8a, system WebView).
- Fork features retained: tappable app icon with six colour schemes, the update-log panel, upstream comparison, automatic reasoning-level fitting, and the plugin native-dependency check.
- Release identity stays independent: package `dsh.android.dev` with this fork's own release certificate, not interchangeable with upstream `dsh.android.client`; upgrading over an existing install requires the same signature.
- The update feed still points at this repository's `updates.json`; APKs are served from this repository's Releases.

This build's `versionCode` is `20050357`. Users on an older build will not see it under "check for updates" (the updater requires a larger versionCode) and must download and install it manually.
Actual software checks and on-device acceptance are limited to this round's delivery receipt and do not prove a complete device matrix.""",
    'ru': """Сборка пересобрана на базе DSHA upstream 0.2.2 (build357), включает DSH 0.2.2-rc.1; базовая среда Ubuntu остаётся 10.

- Обновление базы: с upstream 0.2.1-rc.2 (build190) до 0.2.2 (build357), включая мобильный интерфейс v5, отдельную страницу авторизации возможностей устройства и исправление взаимной блокировки регистрации плагинов во время обслуживания.
- Единственный вариант: линия совместимости и GeckoView удалены, выпускается только Standard (Android 11+, arm64-v8a, системный WebView).
- Собственные функции fork сохранены: переключаемая иконка приложения с шестью цветовыми схемами, панель журнала обновлений, сравнение с upstream, автоподбор уровня рассуждений, проверка нативных зависимостей плагинов.
- Идентичность выпуска независима: пакет `dsh.android.dev` и собственный сертификат, несовместимые с upstream `dsh.android.client`; установка поверх требует той же подписи.
- Источник обновлений по-прежнему `updates.json` этого репозитория; APK размещаются в Releases этого репозитория.

`versionCode` этой сборки — `20050357`. Пользователи старой версии не увидят её в «проверке обновлений» (требуется больший versionCode) и должны установить вручную.
Фактические проверки ПО и приёмка на устройстве ограничены отчётом этого раунда и не доказывают полную матрицу устройств.""",
    'ja': """本ビルドは DSHA 上流 0.2.2（build357）を新ベースとして再構築し、DSH 0.2.2-rc.1 を内蔵します。Ubuntu ベース環境は 10 のままです。

- ベース更新：上流 0.2.1-rc.2（build190）から 0.2.2（build357）へ。モバイル UI v5、デバイス機能の許可ページの独立化、メンテナンス時のプラグイン登録デッドロック修正を含みます。
- 単一バリアント：互換ラインと GeckoView を削除し、Standard のみを配布（Android 11 以上、arm64-v8a、システム WebView）。
- 本 fork 独自機能を維持：アイコンをタップして切り替える 6 種類の配色、更新履歴パネル、上流比較、推論レベルの自動適合、プラグインのネイティブ依存チェック。
- リリース識別子は独立：パッケージ名 `dsh.android.dev`、独自のリリース証明書。上流 `dsh.android.client` とは互換性がなく、上書きインストールには同一署名が必要です。
- 更新元は引き続き本リポジトリの `updates.json`、APK は本リポジトリの Releases から配布します。

本ビルドの `versionCode` は `20050357` です。旧版をインストール済みの利用者は「アップデートを確認」に表示されないため（より大きい versionCode が必要）、手動でダウンロードして上書きインストールしてください。
実際のソフトウェア検証と端末検収は本ラウンドの受領記録の範囲に限られ、完全な端末マトリクスを証明するものではありません。""",
    'ko': """이 빌드는 DSHA 업스트림 0.2.2(build357)를 새 기반으로 재구성했으며 DSH 0.2.2-rc.1을 내장합니다. Ubuntu 기본 환경은 10 그대로입니다.

- 기반 업그레이드: 업스트림 0.2.1-rc.2(build190)에서 0.2.2(build357)로. 모바일 UI v5, 기기 기능 권한 페이지 분리, 유지보수 중 플러그인 등록 교착 수정을 포함합니다.
- 단일 변형: 호환 라인과 GeckoView를 제거하고 Standard만 배포합니다(Android 11 이상, arm64-v8a, 시스템 WebView).
- 이 포크의 자체 기능 유지: 아이콘을 눌러 전환하는 6가지 색상, 업데이트 일지 패널, 업스트림 비교, 추론 단계 자동 맞춤, 플러그인 네이티브 의존성 점검.
- 배포 신원은 독립적: 패키지 `dsh.android.dev`, 자체 배포 인증서. 업스트림 `dsh.android.client`와 호환되지 않으며 덮어쓰기 설치에는 동일 서명이 필요합니다.
- 업데이트 소스는 계속 이 저장소의 `updates.json`이며 APK는 이 저장소 Releases에서 제공합니다.

이 빌드의 `versionCode`는 `20050357`입니다. 이전 버전 사용자는 "업데이트 확인"에 이 버전이 보이지 않으며(더 큰 versionCode 필요), 직접 내려받아 덮어쓰기 설치해야 합니다.
실제 소프트웨어 검사와 기기 검수는 이번 라운드의 인수 기록 범위에 한하며 전체 기기 매트릭스를 입증하지 않습니다.""",
    'ar': """أُعيد بناء هذا الإصدار على أساس DSHA upstream 0.2.2 (build357)، ويتضمن DSH 0.2.2-rc.1؛ وتبقى بيئة Ubuntu الأساسية 10.

- ترقية الأساس: من upstream 0.2.1-rc.2 (build190) إلى 0.2.2 (build357)، وتشمل واجهة الهاتف v5، وصفحة مستقلة لتصاريح قدرات الجهاز، وإصلاح حالة الجمود في تسجيل الإضافات أثناء الصيانة.
- نسخة واحدة: أُزيل خط التوافق وGeckoView، ولا يُوزَّع سوى Standard (Android 11 فأحدث، arm64-v8a، WebView النظام).
- الاحتفاظ بميزات هذا الـ fork: أيقونة قابلة للنقر بستة أنظمة ألوان، ولوحة سجل التحديثات، ومقارنة مع upstream، وملاءمة مستوى الاستدلال تلقائيًا، وفحص الاعتماديات الأصلية للإضافات.
- هوية الإصدار مستقلة: الحزمة `dsh.android.dev` وشهادة إصدار خاصة، غير قابلة للتبادل مع `dsh.android.client`؛ التثبيت فوق نسخة قائمة يتطلب التوقيع نفسه.
- مصدر التحديث ما زال `updates.json` في هذا المستودع، وتُقدَّم ملفات APK من Releases هذا المستودع.

قيمة `versionCode` لهذا الإصدار هي `20050357`. لن يرى المستخدمون على نسخة أقدم هذا الإصدار عبر «التحقق من التحديثات» (يلزم versionCode أكبر)، وعليهم التنزيل والتثبيت يدويًا.
تقتصر فحوص البرمجيات والقبول على الجهاز على إيصال هذه الجولة ولا تثبت مصفوفة أجهزة كاملة.""",
    'pt': """Esta compilação foi reconstruída sobre a base DSHA upstream 0.2.2 (build357), incluindo DSH 0.2.2-rc.1; o ambiente base Ubuntu permanece 10.

- Atualização da base: de upstream 0.2.1-rc.2 (build190) para 0.2.2 (build357), incluindo interface móvel v5, página autónoma de autorização de capacidades do dispositivo e a correção do impasse no registo de plugins durante a manutenção.
- Variante única: a linha de compatibilidade e o GeckoView foram removidos; apenas Standard é distribuído (Android 11+, arm64-v8a, WebView do sistema).
- Funcionalidades próprias do fork preservadas: ícone clicável com seis esquemas de cor, painel de registo de atualizações, comparação com upstream, ajuste automático do nível de raciocínio e verificação de dependências nativas de plugins.
- Identidade de lançamento independente: pacote `dsh.android.dev` e certificado próprio, não intercambiável com upstream `dsh.android.client`; instalar por cima exige a mesma assinatura.
- A fonte de atualizações continua a ser o `updates.json` deste repositório; os APK são servidos pelas Releases deste repositório.

O `versionCode` desta compilação é `20050357`. Utilizadores de uma versão anterior não a verão em «verificar atualizações» (é necessário um versionCode maior) e terão de instalar manualmente.
As verificações de software e a aceitação em dispositivo limitam-se ao recibo desta ronda e não provam uma matriz completa de dispositivos.""",
    'la': """Haec aedificatio super basim DSHA upstream 0.2.2 (build357) refecta est, DSH 0.2.2-rc.1 inclusa; basis Ubuntu 10 manet.

- Basis renovata: ab upstream 0.2.1-rc.2 (build190) ad 0.2.2 (build357), inter quae interfacies mobilis v5, pagina propria auctoritatis facultatum machinae, et reparatio obstructionis registrationis pluginorum per tempora maintenance.
- Una varietas: linea compatibilitatis et GeckoView sublatae sunt; sola Standard distribuitur (Android 11 vel superior, arm64-v8a, WebView systematis).
- Propria fork retinita: icon cliccabilis cum sex schematibus colorum, tabula diarii renovationum, comparatio cum upstream, accommodatio gradus ratiocinationis automatica, inspectio dependentiarum nativarum pluginorum.
- Identitas editionis independens: nomen fasciculi `dsh.android.dev` et certificatum proprium, cum upstream `dsh.android.client` non commutanda; installatio super vetus idem signum requirit.
- Fons renovationum manet `updates.json` huius repositorii; APK e Releases huius repositorii praebentur.

`versionCode` huius aedificationis est `20050357`. Qui vetus fasciculum habent hoc in «renovationes inspicere» non videbunt (maior code necessarius est), sed manualiter deponere debent.
Examinationes programmatis et probatio in machina ad tesseras huius circuitus pertinent, nec matricem machinarum completam probant.""",
    'fr': """Cette build est reconstruite sur la base DSHA upstream 0.2.2 (build357) et embarque DSH 0.2.2-rc.1 ; l'environnement de base Ubuntu reste 10.

- Mise à niveau de la base : d'upstream 0.2.1-rc.2 (build190) vers 0.2.2 (build357), avec l'interface mobile v5, une page autonome d'autorisation des capacités de l'appareil et le correctif de blocage d'enregistrement des plugins pendant la maintenance.
- Variante unique : la ligne de compatibilité et GeckoView sont supprimés ; seule Standard est distribuée (Android 11+, arm64-v8a, WebView système).
- Fonctions propres au fork conservées : icône cliquable avec six jeux de couleurs, panneau du journal des mises à jour, comparaison avec upstream, ajustement automatique du niveau de raisonnement, vérification des dépendances natives des plugins.
- Identité de publication indépendante : paquet `dsh.android.dev` et certificat propre, non interchangeables avec upstream `dsh.android.client` ; l'installation par-dessus exige la même signature.
- La source de mise à jour reste `updates.json` de ce dépôt ; les APK sont servis par les Releases de ce dépôt.

Le `versionCode` de cette build est `20050357`. Les utilisateurs d'une version antérieure ne la verront pas dans « rechercher des mises à jour » (un versionCode supérieur est requis) et doivent l'installer manuellement.
Les vérifications logicielles et la recette sur appareil se limitent au reçu de cette campagne et ne prouvent pas une matrice complète d'appareils.""",
}


def main():
    gradle = (ROOT / 'app/build.gradle').read_text(encoding='utf-8')
    code = re.search(r'^\s*versionCode\s+(\d+)\s*$', gradle, re.M)
    version = re.search(r'^\s*versionName\s+"([^"\r\n]+)"\s*$', gradle, re.M)
    if not code or not version:
        raise SystemExit('BUILD_IDENTITY_MISSING')
    code, version = int(code.group(1)), version.group(1)
    # 与上游 tools/generate-changelog.py 的 heading 完全一致，不要自行加前缀。
    heading = '# DSHA %s / build%d' % (version, code)
    written = 0
    for locale in LOCALES:
        body = BODY.get(locale)
        if not body:
            raise SystemExit('LOCALE_BODY_MISSING: ' + locale)
        path = ROOT / ('docs/releases/build%d-changes.%s.md' % (code, locale))
        path.write_text(heading + '\n\n' + body.strip() + '\n', encoding='utf-8')
        written += 1
    print('已生成 %d 个语言的更新记录：%s' % (written, heading))


if __name__ == '__main__':
    main()
