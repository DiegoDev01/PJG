# Manual de Produção - Canal Dark GTA 6 (Projeto D:\PJG)

## 1. Hardware & Performance (Windows 11 Pro + AMD RX 7600)
- **Renderização GPU:** Sempre usar aceleração AMD AMF (-c:v h264_amf -usage transcoding -quality speed -rc cqp -qp_i 19 -qp_p 19 -pix_fmt yuv420p) em 1080x1920 a 60fps.
- **Alinhamento de Voz e Legenda:** Usar aster-whisper (device="cpu", compute_type="int8", language="pt", word_timestamps=True) apenas no áudio da narração em ./02_narracao_e_roteiro/.
- **Correção pelo Roteiro:** Cruzar os timestamps do Whisper com o .txt do roteiro oficial para garantir ortografia perfeita de nomes próprios (Lucia, Jason, Vice City, Leonida) sem perder os milissegundos exatos.

## 2. Estrutura de Pastas (Raiz: D:\PJG)
- ./01_gameplay_bruta/ -> Vídeos brutos de GTA 6.
- ./02_narracao_e_roteiro/ -> Pares de áudio e texto (ex: corte01.mp3 e corte01.txt).
- ./03_legendas_sync/ -> Arquivos .ass e .json gerados automaticamente.
- ./04_cortes_prontos/ -> Vídeos finais prontos para postar.
- ./05_assets/fontes/ -> Fontes .ttf (Montserrat-ExtraBold.ttf).
- ./scripts/ -> Scripts Python de automação.

## 3. Padrão Visual e Áudio (Canal Dark - Sem Webcam)
- **Layout 9:16 (1080x1920):** Fundo desfocado (gblur=sigma=35, eq=brightness=-0.15) + Gameplay centralizada (1080x608).
- **Legendas Dinâmicas (.ass):** Blocos de 2 a 3 palavras em caixa alta, fonte Montserrat-ExtraBold.ttf em ./05_assets/fontes/, destaque em amarelo (#FFD700), borda preta grossa (Outline=4), centralizada abaixo da gameplay (y=1320).
- **Áudio:** Cortar pausas maiores que 0.35s na narração. Manter voz em -3dB e som do jogo ao fundo bem baixo (-22dB).
