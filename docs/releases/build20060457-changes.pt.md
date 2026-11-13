# DSHA v1.5 20261113@0.2.2-rc.1・ build20060457

- Corrigido: o ícone do aplicativo no cabeçalho da página de atualização e nos gerenciadores de arquivos não acompanhava o esquema de cores — estava fixo na imagem padrão antiga.
- O separador de versão agora é o ponto médio de largura total ・. O marcador sólido anterior fica baixo por desenho e nunca alinhava com os dígitos ao lado; trocar o caractere é mais confiável do que corrigir a linha de base, e nenhum contorno permanece.
- Corrigido o "verificar atualizações" que sempre dizia não haver atualização: a validação do nome de versão herdava um padrão do upstream que rejeita espaço e @, enquanto o nome aqui é `v1.5 20261112@0.2.2-rc.1`; a nossa própria versão era descartada pela nossa própria validação, em silêncio.
- A leitura da lista de atualizações agora tenta novamente: os tempos limite já existiam (15 s conexão / 30 s leitura), mas uma única falha de rede exigia nova tentativa manual. Até três tentativas com espera de 1 s / 2 s, apenas para erros transitórios; erros de certificado e de formato não são repetidos.
- O modo de segurança agora bloqueia instalar e ativar plugins: antes afetava apenas a faixa visível enquanto instalar e ativar continuavam funcionando. Desativar e desinstalar seguem permitidos.
- Corrigido o botão de entrada no Web travado em "abrindo…" após a mudança de geração do Web: a mudança de geração significa que a geração aguardada desapareceu. Agora volta ao estado repetível com "Web reiniciado, abra novamente" em vez de ser tratado como falha.
- A tela virtual agora amortece rejeições consecutivas de quadro: rejeições ocasionais são normais, mas três seguidas indicam que a sequência de quadros não corresponde mais à imagem; a sessão antiga é descartada e recriada.
- Corrigida a caixa de notas de versão exibindo "esta instalação não inclui notas para a compilação atual": após a troca do separador no gerador de título, o lado leitor ainda comparava pelo formato antigo.
