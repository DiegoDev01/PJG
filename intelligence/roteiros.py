from database.database import SessionLocal
from database.models import Pauta
from intelligence.providers.factory import criar_provedor


def gerar_roteiro(
    titulo: str,
    conteudo: str,
    formato: str = "short",
    fonte: str = "",
    classificacao: str = "pendente"
) -> dict:

    ia = criar_provedor()

    if not ia.verificar_conexao():
        raise RuntimeError("Ollama não está disponível.")

    # ETAPA 1: Extração de evidências
    prompt_analise = f"""
Você é um analista editorial rigoroso do canal Pela Janela Games.

Sua tarefa é analisar o material fornecido sem acrescentar
nenhuma informação externa.

TÍTULO:
{titulo}

CONTEÚDO ORIGINAL:
{conteudo}

FONTE:
{fonte}

CLASSIFICAÇÃO INICIAL:
{classificacao}

REGRAS OBRIGATÓRIAS:

1. Utilize exclusivamente o conteúdo original.
2. Não pesquise nem invente informações.
3. Não trate afirmações da fonte como verificadas independentemente.
4. Não transforme uma informação ausente em uma conclusão.
5. Não invente datas, números, recomendações ou declarações.
6. Não deduza motivos ou consequências.
7. Quando algo não estiver explícito, escreva "NÃO INFORMADO".
8. Preserve a diferença entre fatos relatados, rumores e especulações.

FORMATO DA ANÁLISE:

1. AFIRMAÇÕES EXPLÍCITAS DA FONTE:
Liste somente informações diretamente presentes no texto.

2. EVIDÊNCIAS ORIGINAIS:
Para cada afirmação, apresente um pequeno trecho literal
do conteúdo que a sustenta.

3. RUMORES E ESPECULAÇÕES:
Identifique apenas os que aparecem explicitamente no material.

4. INFORMAÇÕES AUSENTES:
Liste detalhes importantes que não foram fornecidos.

5. INFORMAÇÕES NÃO VERIFICADAS INDEPENDENTEMENTE:
Informe que o conteúdo não foi verificado fora da fonte.

6. LIMITES EDITORIAIS:
Liste tudo que o roteiro não poderá afirmar.

Não complete lacunas com conhecimento próprio.
Entregue somente a análise.
"""

    analise = ia.gerar_texto(prompt_analise)

    # ETAPA 2: Criação do roteiro
    if formato == "short":

        prompt_roteiro = f"""
Você é roteirista do canal brasileiro Pela Janela Games.

Crie um YouTube Short utilizando exclusivamente
as evidências presentes na análise editorial.

TÍTULO:
{titulo}

FONTE:
{fonte}

ANÁLISE EDITORIAL:
{analise}

REGRAS INEGOCIÁVEIS:

1. Não acrescente nenhum fato que não esteja na análise.
2. Não utilize conhecimento externo.
3. Não invente recomendações, avisos ou declarações.
4. Não invente datas ou números.
5. Não transforme afirmações da fonte em fatos
   verificados independentemente.
6. Não crie perguntas insinuantes.
7. Não invente consequências ou motivos.
8. Não utilize informações da seção INFORMAÇÕES AUSENTES
   como se fossem fatos.
9. Se houver pouca informação, faça um roteiro mais curto.
10. Nunca invente conteúdo para atingir a duração desejada.

ESTILO:

- Português brasileiro natural.
- Linguagem acessível.
- Tom informativo e envolvente.
- Humor somente quando sustentado pelo conteúdo.
- Sem sensacionalismo.

DURAÇÃO:
Busque 35 a 55 segundos, mas a fidelidade é mais importante
que a duração.

ESTRUTURA:

[excited] Chega mais perto da janela!

[curious] Apresente a informação principal.

[serious] Explique somente o que a fonte efetivamente informou.

[ curious] Apresente um contexto permitido pelas evidências,
somente se existir.

[happy] Pela Janela Games!
A gente não joga tudo, mas acompanha tudo!

IMPORTANTE:

Se a análise não apresentar informações suficientes,
não invente uma conclusão ou pergunta.

Entregue somente o roteiro.
"""

    else:

        prompt_roteiro = f"""
Você é roteirista do canal Pela Janela Games.

Crie um roteiro para vídeo longo utilizando exclusivamente
as evidências da análise editorial.

TÍTULO:
{titulo}

FONTE:
{fonte}

ANÁLISE EDITORIAL:
{analise}

REGRAS:

- Não acrescente fatos externos.
- Não invente declarações ou recomendações.
- Não transforme afirmações da fonte em confirmação independente.
- Diferencie fatos relatados, rumores e especulações.
- Respeite todas as limitações editoriais da análise.
- Não preencha lacunas com suposições.
- Se faltarem informações, deixe isso claro.
- Utilize marcações emocionais para ElevenLabs.

Entregue somente o roteiro.
"""

    roteiro = ia.gerar_texto(prompt_roteiro)

    return {
        "titulo": titulo,
        "formato": formato,
        "analise": analise,
        "roteiro": roteiro
    }


def gerar_roteiro_aprovado(pauta_id: int, formato: str = "short"):

    sessao = SessionLocal()

    try:
        pauta = sessao.get(Pauta, pauta_id)

        if pauta is None:
            raise ValueError("Pauta não encontrada.")

        if pauta.status != "aprovada":
            raise ValueError("Esta pauta ainda não foi aprovada.")

        return gerar_roteiro(
            titulo=pauta.titulo,
            conteudo=pauta.assunto,
            formato=formato,
            fonte=pauta.fonte or "",
            classificacao=pauta.classificacao
        )

    finally:
        sessao.close()