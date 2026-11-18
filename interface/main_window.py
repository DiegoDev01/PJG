import tkinter as tk
import threading

from tkinter import ttk, messagebox

from database.database import SessionLocal
from database.models import Pauta

from intelligence.pesquisa import (
    pesquisar_noticias,
    salvar_noticias
)

from intelligence.aprovacao import atualizar_status
from intelligence.roteiros import gerar_roteiro_aprovado


class MainWindow:

    def __init__(self, root):
        self.root = root
        self.root.title("Pela Janela Games - PJG 2.0")
        self.root.geometry("1100x700")
        self.root.minsize(850, 550)

        self.processando = False

        self.criar_interface()
        self.carregar_pautas()

    def criar_interface(self):

        ttk.Label(
            self.root,
            text="PELA JANELA GAMES",
            font=("Arial", 20, "bold")
        ).pack(pady=15)

        ttk.Label(
            self.root,
            text="Central de Inteligência e Produção"
        ).pack()

        self.tabela = ttk.Treeview(
            self.root,
            columns=("id", "relevancia", "titulo", "fonte", "status"),
            show="headings"
        )

        colunas = [
            ("id", "ID", 50),
            ("relevancia", "Relevância", 90),
            ("titulo", "Notícia", 550),
            ("fonte", "Fonte", 180),
            ("status", "Status", 120)
        ]

        for coluna, nome, largura in colunas:
            self.tabela.heading(coluna, text=nome)
            self.tabela.column(coluna, width=largura)

        self.tabela.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=15
        )

        botoes = ttk.Frame(self.root)
        botoes.pack(pady=10)

        self.botao_atualizar = ttk.Button(
            botoes,
            text="Atualizar",
            command=self.atualizar_noticias
        )
        self.botao_atualizar.pack(side="left", padx=5)

        self.botao_aprovar = ttk.Button(
            botoes,
            text="Aprovar pauta",
            command=lambda: self.alterar_status("aprovada")
        )
        self.botao_aprovar.pack(side="left", padx=5)

        self.botao_rejeitar = ttk.Button(
            botoes,
            text="Rejeitar pauta",
            command=lambda: self.alterar_status("rejeitada")
        )
        self.botao_rejeitar.pack(side="left", padx=5)

        self.botao_roteiro = ttk.Button(
            botoes,
            text="Gerar roteiro",
            command=self.gerar_roteiro
        )
        self.botao_roteiro.pack(side="left", padx=5)

    def carregar_pautas(self):

        for item in self.tabela.get_children():
            self.tabela.delete(item)

        sessao = SessionLocal()

        try:
            pautas = (
                sessao.query(Pauta)
                .filter(Pauta.status.in_(["aguardando", "aprovada"]))
                .order_by(Pauta.relevancia.desc())
                .all()
            )

            for pauta in pautas:
                self.tabela.insert(
                    "",
                    "end",
                    values=(
                        pauta.id,
                        pauta.relevancia,
                        pauta.titulo,
                        pauta.fonte,
                        pauta.status
                    )
                )

        finally:
            sessao.close()

    def obter_pauta_selecionada(self):

        selecionado = self.tabela.selection()

        if not selecionado:
            messagebox.showwarning(
                "Atenção",
                "Selecione uma pauta primeiro."
            )
            return None

        valores = self.tabela.item(selecionado[0])["values"]

        return int(valores[0]), valores[4]

    def definir_processamento(self, ativo):

        self.processando = ativo

        estado = "disabled" if ativo else "normal"

        self.botao_atualizar.config(state=estado)
        self.botao_aprovar.config(state=estado)
        self.botao_rejeitar.config(state=estado)
        self.botao_roteiro.config(state=estado)

        self.root.config(
            cursor="wait" if ativo else ""
        )

    def atualizar_noticias(self):

        if self.processando:
            return

        self.definir_processamento(True)

        janela = self.criar_janela_progresso(
            "Atualizando notícias",
            "Pesquisando fontes e salvando pautas..."
        )

        def processar():

            try:
                noticias = pesquisar_noticias()
                novas = salvar_noticias(noticias)

                self.root.after(
                    0,
                    lambda: self.finalizar_pesquisa(
                        janela,
                        len(noticias),
                        novas
                    )
                )

            except Exception as erro:
                mensagem = str(erro)

                self.root.after(
                    0,
                    lambda: self.finalizar_erro(
                        janela,
                        "Erro na pesquisa",
                        mensagem
                    )
                )

        threading.Thread(
            target=processar,
            daemon=True
        ).start()

    def finalizar_pesquisa(self, janela, encontradas, novas):

        janela.destroy()

        self.carregar_pautas()
        self.definir_processamento(False)

        messagebox.showinfo(
            "PJG",
            f"Pesquisa concluída!\n\n"
            f"Encontradas: {encontradas}\n"
            f"Novas pautas salvas: {novas}"
        )

    def alterar_status(self, status):

        if self.processando:
            return

        selecionada = self.obter_pauta_selecionada()

        if selecionada is None:
            return

        pauta_id, status_atual = selecionada

        if status_atual != "aguardando":
            messagebox.showwarning(
                "PJG",
                "Somente pautas aguardando aprovação podem ser alteradas."
            )
            return

        if atualizar_status(pauta_id, status):
            self.carregar_pautas()

            messagebox.showinfo(
                "PJG",
                f"Pauta {status} com sucesso!"
            )

    def criar_janela_progresso(self, titulo, mensagem):

        janela = tk.Toplevel(self.root)
        janela.title(titulo)
        janela.geometry("420x160")
        janela.resizable(False, False)
        janela.transient(self.root)

        ttk.Label(
            janela,
            text=mensagem,
            wraplength=370,
            justify="center"
        ).pack(pady=20)

        progresso = ttk.Progressbar(
            janela,
            mode="indeterminate"
        )

        progresso.pack(
            fill="x",
            padx=25,
            pady=10
        )

        progresso.start(10)

        janela.progresso = progresso

        return janela

    def gerar_roteiro(self):

        if self.processando:
            return

        selecionada = self.obter_pauta_selecionada()

        if selecionada is None:
            return

        pauta_id, status = selecionada

        if status != "aprovada":
            messagebox.showwarning(
                "PJG",
                "Aprove a pauta antes de gerar o roteiro."
            )
            return

        self.definir_processamento(True)

        janela = self.criar_janela_progresso(
            "Gerando roteiro",
            "A inteligência artificial está trabalhando.\n"
            "Isso pode levar alguns instantes."
        )

        def processar():

            try:
                resultado = gerar_roteiro_aprovado(pauta_id)

                self.root.after(
                    0,
                    lambda: self.finalizar_roteiro(
                        resultado,
                        janela
                    )
                )

            except Exception as erro:

                mensagem = str(erro)

                self.root.after(
                    0,
                    lambda: self.finalizar_erro(
                        janela,
                        "Erro na geração do roteiro",
                        mensagem
                    )
                )

        threading.Thread(
            target=processar,
            daemon=True
        ).start()

    def finalizar_roteiro(self, resultado, janela):

        janela.destroy()

        self.definir_processamento(False)

        janela_resultado = tk.Toplevel(self.root)
        janela_resultado.title("Análise e roteiro PJG")
        janela_resultado.geometry("850x700")

        abas = ttk.Notebook(janela_resultado)
        abas.pack(fill="both", expand=True, padx=10, pady=10)

        # Aba de análise
        aba_analise = ttk.Frame(abas)
        abas.add(aba_analise, text="Análise da IA")

        texto_analise = tk.Text(
            aba_analise,
            wrap="word",
            font=("Arial", 11)
        )
        texto_analise.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        texto_analise.insert("1.0", resultado["analise"])
        texto_analise.config(state="disabled")

        # Aba de roteiro
        aba_roteiro = ttk.Frame(abas)
        abas.add(aba_roteiro, text="Roteiro")

        texto_roteiro = tk.Text(
            aba_roteiro,
            wrap="word",
            font=("Arial", 11)
        )
        texto_roteiro.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        texto_roteiro.insert("1.0", resultado["roteiro"])
        texto_roteiro.config(state="disabled")

    def finalizar_erro(self, janela, titulo, mensagem):

        janela.destroy()

        self.definir_processamento(False)

        messagebox.showerror(
            titulo,
            mensagem
        )


def iniciar_interface():

    root = tk.Tk()

    MainWindow(root)

    root.mainloop()