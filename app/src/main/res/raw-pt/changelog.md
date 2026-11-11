# DSHA v1.4 20261111@0.2.2-rc.1. build20050357

Esta compilação foi reconstruída sobre o upstream DSHA 0.2.2 (upstream build357), com DSH 0.2.2-rc.1 na base Ubuntu 10.

- Corrigida a página inicial em branco após a atualização, o botão «Iniciar DSHA» sem resposta e travamentos ocasionais na página de recuperação.
- Corrigido o travamento permanente da manutenção em «parar Web e tarefas de terminal», em que «Tentar novamente» não ajudava: a barreira de paragem não reconhecia o supervisor de contentor lançado pelo próprio aplicativo e tratava-o como processo não identificado.
- Corrigido o estado «identidade desconhecida» que impedia o arranque após atualizar ou reinstalar uma versão anterior do APK: foi adicionado um critério de troca de compilação que trata a substituição do pacote como expiração definida e segue para a página de instalação e reparação.
- Adicionada adaptação automática do nível de raciocínio: modelos sem nível declarado recebem a declaração (a DSHA não adivinha que níveis um modelo de terceiros suporta; sem declaração, o nível não é mostrado). Apenas adiciona, com cópia de segurança automática da configuração antes de escrever.
- O ícone do aplicativo pode ser tocado para alternar entre seis paletas; a alteração aplica-se de imediato e é memorizada. O ícone da página «Sobre» e o da caixa de diálogo têm a mesma origem, tocar abre o seletor e o ícone preenche a área.
- As dicas de capacidades dos plugins ganharam uma verificação de dependências nativas: leitura apenas do ABI e do cabeçalho dos módulos nativos incluídos, com aviso que não bloqueia a instalação.
- Adicionado o painel de registo de atualizações: a página «Sobre» mostra as versões em blocos, com possibilidade de expandir tudo; a caixa de diálogo «Sobre a DSHA» inclui o mesmo registo.
- Adicionada a comparação com o upstream: mostra se o código difere do upstream, apenas leitura, nunca escrita.
- O contacto na página «Sobre» passou a ser o e-mail steveneng@163.com; o link «ver versões no navegador» e os canais stable e preview apontam para este repositório e não para a página de versões do upstream.
- A identidade de publicação mantém-se independente: pacote dsh.android.dev e certificado próprio, incompatível com o upstream dsh.android.client; instalar por cima exige a mesma assinatura.
- Variante única: a linha de compatibilidade e o GeckoView foram removidos; apenas Standard é publicado (Android 11+, arm64-v8a, WebView do sistema).
- Fundido com o upstream DSHA 0.2.2 (upstream build357), com DSH 0.2.2-rc.1 e base Ubuntu 10: interface móvel v5, página autónoma de autorização de capacidades do dispositivo, correção do bloqueio de registo de plugins durante a manutenção e todos os commits do upstream desde a fusão anterior (upstream v0.2.1-rc.2, upstream build190). O ramo foi reconstruído sobre um commit real do upstream (5e2dca92, 2026-11-11), pelo que as próximas atualizações fundem diretamente.
