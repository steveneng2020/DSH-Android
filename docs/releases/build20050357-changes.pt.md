# DSHA v1.4 20261111@0.2.2-rc.1 / build20050357

Esta compilação foi reconstruída sobre a base DSHA upstream 0.2.2 (build357), incluindo DSH 0.2.2-rc.1; o ambiente base Ubuntu permanece 10.

- Atualização da base: de upstream 0.2.1-rc.2 (build190) para 0.2.2 (build357), incluindo interface móvel v5, página autónoma de autorização de capacidades do dispositivo e a correção do impasse no registo de plugins durante a manutenção.
- Variante única: a linha de compatibilidade e o GeckoView foram removidos; apenas Standard é distribuído (Android 11+, arm64-v8a, WebView do sistema).
- Funcionalidades próprias do fork preservadas: ícone clicável com seis esquemas de cor, painel de registo de atualizações, comparação com upstream, ajuste automático do nível de raciocínio e verificação de dependências nativas de plugins.
- Identidade de lançamento independente: pacote `dsh.android.dev` e certificado próprio, não intercambiável com upstream `dsh.android.client`; instalar por cima exige a mesma assinatura.
- A fonte de atualizações continua a ser o `updates.json` deste repositório; os APK são servidos pelas Releases deste repositório.

O `versionCode` desta compilação é `20050357`. Utilizadores de uma versão anterior não a verão em «verificar atualizações» (é necessário um versionCode maior) e terão de instalar manualmente.
As verificações de software e a aceitação em dispositivo limitam-se ao recibo desta ronda e não provam uma matriz completa de dispositivos.
