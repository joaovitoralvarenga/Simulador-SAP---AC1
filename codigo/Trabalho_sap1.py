import tkinter as tk
from tkinter import ttk, messagebox
import time
import re

CAPACIDADE_MEMORIA = 16

class NucleoSAP1:
    def __init__(self):
        self.registradores = {
            "ContadorPrograma": 0,
            "Acumulador": 0,
            "RegistradorEndereco": 0,
            "RegistradorInstrucao": 0,
            "RegistradorB": 0,
            "RegistradorSaida": 0,
            "Flags": {"Zero": 0, "Carry": 0}
        }
        self.memoria_principal = [0] * CAPACIDADE_MEMORIA

        self.conjunto_instrucoes = {
            0b0000: ("CAR", self._executar_car),
            0b0001: ("SOM", self._executar_som),
            0b0010: ("SUB", self._executar_sub),
            0b1110: ("SAI", self._executar_sai),
            0b1111: ("PAR", self._executar_par)
        }

    def _executar_car(self, operando):
        self.registradores['RegistradorEndereco'] = operando
        self.registradores['Acumulador'] = self.memoria_principal[self.registradores['RegistradorEndereco']]
        return False

    def _executar_som(self, operando):
        self.registradores['RegistradorEndereco'] = operando
        self.registradores['RegistradorB'] = self.memoria_principal[self.registradores['RegistradorEndereco']]
        self.registradores['Acumulador'] = (self.registradores['Acumulador'] + self.registradores['RegistradorB']) & 0xFF
        return False

    def _executar_sub(self, operando):
        self.registradores['RegistradorEndereco'] = operando
        self.registradores['RegistradorB'] = self.memoria_principal[self.registradores['RegistradorEndereco']]
        self.registradores['Acumulador'] = (self.registradores['Acumulador'] - self.registradores['RegistradorB']) & 0xFF
        return False

    def _executar_sai(self, _):
        self.registradores['RegistradorSaida'] = self.registradores['Acumulador']
        return False

    def _executar_par(self, _):
        return True

class AplicativoSimulador:
    def __init__(self, janela_principal):
        self.janela_principal = janela_principal
        self.janela_principal.title("Simulador SAP-1")
        self.janela_principal.geometry("1000x750")
        self.janela_principal.configure(bg='#000000')  # Fundo preto

        self.nucleo = NucleoSAP1()
        self.executando = False
        self.velocidade_simulacao = 1.0

        self.valor_campo_expressao = tk.StringVar(value="")
        self.linha_codigo_atual = -1

        self._configurar_estilos()
        self._construir_interface()
        self.reiniciar_simulador()

    def _configurar_estilos(self):
        estilo = ttk.Style()
        estilo.theme_use('clam')

        estilo.configure('TFrame', background='#f0f0f5')
        estilo.configure('TLabel', background='#f0f0f5', font=('Arial', 9))
        estilo.configure('TButton',
                        font=('Arial', 9, 'bold'),
                        foreground='#333355',
                        background='#d0d0ff',
                        padding=6,
                        relief='raised',
                        borderwidth=2)
        estilo.map('TButton',
                  background=[('active', '#a0a0ff'), ('pressed', '#8888ff')],
                  foreground=[('active', 'white'), ('pressed', 'white')])

        estilo.configure('TLabelFrame', background='#f0f0f5', foreground='#333355', font=('Arial', 10, 'bold'))
        estilo.configure('Horizontal.TScale', background='#f0f0f5', troughcolor='#c0c0ff')

    def _construir_interface(self):
        container_principal = ttk.Frame(self.janela_principal, padding="10")
        container_principal.pack(fill=tk.BOTH, expand=True)

        painel_esquerdo = ttk.Frame(container_principal, width=350)
        painel_esquerdo.pack(fill=tk.BOTH, side=tk.LEFT, padx=5, pady=5)
        painel_esquerdo.pack_propagate(False)

        secao_expressao = ttk.LabelFrame(painel_esquerdo, text="Entrada de Expressão", padding="10")
        secao_expressao.pack(fill=tk.X, pady=5)

        ttk.Label(secao_expressao, text="Digite a Expressão:", font=('Arial', 9, 'bold')).pack(anchor='w', pady=(0, 4))
        ttk.Entry(secao_expressao, textvariable=self.valor_campo_expressao, state='readonly', font=('Consolas', 12), width=30, justify='right', background='#2c3e50').pack(fill=tk.X, pady=5)

        frame_teclado = ttk.Frame(secao_expressao)
        frame_teclado.pack(pady=5)

        digitos = ['7', '8', '9', '+', '4', '5', '6', '-', '1', '2', '3', '0']
        for i, digito in enumerate(digitos):
            ttk.Button(frame_teclado, text=digito, command=lambda val=digito: self._tecla_expressao(val), width=4).grid(row=i//4, column=i%4, padx=3, pady=3)

        frame_botoes = ttk.Frame(secao_expressao)
        frame_botoes.pack(fill=tk.X, pady=5)
        ttk.Button(frame_botoes, text="Gerar Código", command=self._processar_expressao).pack(side=tk.LEFT, expand=True, padx=3)
        ttk.Button(frame_botoes, text="Limpar", command=self._limpar_expressao).pack(side=tk.LEFT, expand=True, padx=3)

        secao_editor = ttk.LabelFrame(painel_esquerdo, text="Editor de Código", padding="10")
        secao_editor.pack(fill=tk.BOTH, expand=True, pady=5)

        self.area_texto = tk.Text(secao_editor, wrap=tk.NONE, width=30, height=10,
                                 font=('Consolas', 11), relief="sunken", borderwidth=1, bg='#2c3e50', fg='#ffffff')
        self.area_texto.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scrollbar = ttk.Scrollbar(secao_editor, orient=tk.VERTICAL, command=self.area_texto.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.area_texto['yscrollcommand'] = scrollbar.set

        painel_controle = ttk.Frame(painel_esquerdo, padding=(0, 10))
        painel_controle.pack(fill=tk.X, pady=5)

        ttk.Button(painel_controle, text="Montar Programa", command=self._montar_codigo).pack(fill=tk.X, pady=3)
        ttk.Button(painel_controle, text="Executar", command=self._iniciar_simulacao).pack(fill=tk.X, pady=3)
        ttk.Button(painel_controle, text="Passo a Passo", command=self._executar_passo).pack(fill=tk.X, pady=3)
        ttk.Button(painel_controle, text="Reiniciar", command=self.reiniciar_simulador).pack(fill=tk.X, pady=3)

        frame_velocidade = ttk.LabelFrame(painel_controle, text="", padding="8")
        frame_velocidade.pack(fill=tk.X, pady=10)
        self.controle_velocidade = ttk.Scale(frame_velocidade, from_=0.1, to=2.0, value=1.0,
                                    command=self._atualizar_velocidade,
                                    orient=tk.HORIZONTAL, length=200)
        self.controle_velocidade.pack(fill=tk.X, pady=5)

        painel_cpu = ttk.LabelFrame(container_principal, text="Visualização da CPU", padding="10")
        painel_cpu.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=5, pady=5)

        self.canvas_cpu = tk.Canvas(painel_cpu, width=600, height=550, bg="#1a1a1a", relief="groove", borderwidth=2, highlightthickness=0)
        self.canvas_cpu.pack(fill=tk.BOTH, expand=True)

        self.mensagem_status = tk.StringVar()
        self.mensagem_status.set("Pronto.")
        barra_status = ttk.Label(self.janela_principal, textvariable=self.mensagem_status,
                             relief=tk.SUNKEN, padding="6", font=('Arial', 9), anchor='w', 
                             background='#8e44ad', foreground='white')
        barra_status.pack(fill=tk.X, side=tk.BOTTOM)

        self._desenhar_cpu()

        self.area_texto.tag_configure("linha_ativa", background="#8e44ad", foreground="white")
        self.area_texto.tag_configure("erro", background="#e74c3c", foreground="white")

    def _desenhar_cpu(self):
        self.canvas_cpu.delete("all")

        cor_componente = "#2c3e50"
        cor_borda = "#9b59b6"
        cor_barramento = "#8e44ad"
        cor_sombra = "#34495e"
        cor_texto = "#ffffff"

        def criar_componente(x, y, largura, altura, rotulo, tag, valor):
            self.canvas_cpu.create_rectangle(x + 4, y + 4, x + largura + 4, y + altura + 4, fill=cor_sombra, tags=f"{tag}_sombra", outline="")
            self.canvas_cpu.create_rectangle(x, y, x + largura, y + altura, fill=cor_componente, outline=cor_borda, width=2, tags=tag)
            self.canvas_cpu.create_text(x + largura/2, y + altura/3, text=rotulo, font=('Arial', 10, 'bold'), fill=cor_texto)
            self.canvas_cpu.create_text(x + largura/2, y + 2*altura/3, text=valor, font=('Consolas', 11), tags=f"{tag}_val", fill=cor_texto)

        POSICAO_BARRA_Y = 400
        self.canvas_cpu.create_line(50, POSICAO_BARRA_Y, 800, POSICAO_BARRA_Y, width=3, fill=cor_barramento, tags="barramento")

        criar_componente(100, 50, 100, 70, "CP", "bloco_cp", "0x0")
        self.canvas_cpu.create_line(150, 120, 150, POSICAO_BARRA_Y, width=1, fill=cor_barramento, tags="conexao_cp")

        criar_componente(250, 50, 100, 70, "REM", "bloco_rem", "0x0")
        self.canvas_cpu.create_line(300, 120, 300, POSICAO_BARRA_Y, width=1, fill=cor_barramento, tags="conexao_rem")

        criar_componente(450, 50, 100, 70, "RI", "bloco_ri", "0x00")
        self.canvas_cpu.create_text(500, 35, text="(Opcode | Operando)", font=('Arial', 8), fill="#bdc3c7")
        self.canvas_cpu.create_line(500, 120, 500, POSICAO_BARRA_Y, width=1, fill=cor_barramento, tags="conexao_ri")

        criar_componente(100, 200, 100, 70, "ACC", "bloco_acc", "0x00")
        self.canvas_cpu.create_line(150, 270, 150, POSICAO_BARRA_Y, width=1, fill=cor_barramento, tags="conexao_acc")
        self.canvas_cpu.create_line(200, 235, 250, 235, width=1, fill=cor_barramento, tags="conexao_acc_alu")

        criar_componente(250, 200, 100, 70, "Reg B", "bloco_regb", "0x00")
        self.canvas_cpu.create_line(300, 270, 300, POSICAO_BARRA_Y, width=1, fill=cor_barramento, tags="conexao_regb")
        self.canvas_cpu.create_line(350, 235, 400, 235, width=1, fill=cor_barramento, tags="conexao_regb_alu")

        criar_componente(400, 200, 150, 70, "ULA", "bloco_ula", "")
        self.canvas_cpu.create_line(475, 270, 475, POSICAO_BARRA_Y, width=1, fill=cor_barramento, tags="conexao_ula")
        self.canvas_cpu.create_text(475, 235, text="±", font=('Arial', 18, 'bold'), fill=cor_texto, tags="simbolo_ula")

        RAM_X = 600
        RAM_Y = 50
        RAM_LARGURA = 180
        RAM_ALTURA = 280
        self.canvas_cpu.create_rectangle(RAM_X + 4, RAM_Y + 4, RAM_X + RAM_LARGURA + 4, RAM_Y + RAM_ALTURA + 4, fill=cor_sombra, tags="ram_sombra", outline="")
        self.canvas_cpu.create_rectangle(RAM_X, RAM_Y, RAM_X + RAM_LARGURA, RAM_Y + RAM_ALTURA, fill="#2c3e50", outline=cor_borda, width=2, tags="ram")
        self.canvas_cpu.create_text(RAM_X + RAM_LARGURA/2, RAM_Y - 20, text="RAM (16 Bytes)", font=('Arial', 11, 'bold'), fill=cor_texto)
        self.canvas_cpu.create_line(RAM_X + RAM_LARGURA/2, RAM_Y + RAM_ALTURA, RAM_X + RAM_LARGURA/2, POSICAO_BARRA_Y, width=1, fill=cor_barramento, tags="conexao_ram")

        self.celulas_ram = []
        self.textos_ram = []
        self.enderecos_ram = []

        largura_celula = 35
        altura_celula = 30
        espacamento_x = 7
        espacamento_y = 7
        inicio_x = RAM_X + 10
        inicio_y = RAM_Y + 30

        for i in range(CAPACIDADE_MEMORIA):
            col = i % 4
            lin = i // 4
            x1 = inicio_x + col * (largura_celula + espacamento_x)
            y1 = inicio_y + lin * (altura_celula + espacamento_y)
            x2 = x1 + largura_celula
            y2 = y1 + altura_celula

            celula = self.canvas_cpu.create_rectangle(x1, y1, x2, y2, fill="#34495e", tags=f"celula_ram_{i}", width=1, outline="#7f8c8d")
            self.celulas_ram.append(celula)

            texto = self.canvas_cpu.create_text(x1 + largura_celula/2, y1 + altura_celula/2, text="00", tags=f"valor_ram_{i}", font=('Consolas', 9, 'bold'), fill=cor_texto)
            self.textos_ram.append(texto)

            endereco = self.canvas_cpu.create_text(x1 + largura_celula/2, y1 - 10, text=f"{i:01X}", tags=f"endereco_ram_{i}", font=('Arial', 7), fill="#bdc3c7")
            self.enderecos_ram.append(endereco)

        criar_componente(100, 500, 100, 70, "SAÍDA", "bloco_saida", "0x00")
        self.canvas_cpu.create_line(150, 500, 150, POSICAO_BARRA_Y, width=1, fill=cor_barramento, tags="conexao_saida")

        POSICAO_LED_X = 100
        POSICAO_LED_Y = 600
        self.leds_saida = []
        for i in range(8):
            x = POSICAO_LED_X + i * 20
            led = self.canvas_cpu.create_oval(x, POSICAO_LED_Y, x+15, POSICAO_LED_Y+15, fill="#34495e", outline="#7f8c8d")
            self.leds_saida.append(led)
            self.canvas_cpu.create_text(x+7, POSICAO_LED_Y+25, text=f"B{7-i}", font=('Arial', 7), fill='#bdc3c7')

        self.canvas_cpu.create_rectangle(650, 480, 720, 530, fill="#2c3e50", outline=cor_borda, width=2, tags="relogio")
        self.canvas_cpu.create_text(685, 505, text="CLOCK", tags="texto_relogio", font=('Arial', 10, 'bold'), fill=cor_texto)

    def _tecla_expressao(self, tecla):
        valor_atual = self.valor_campo_expressao.get()
        if tecla in ['+', '-']:
            if not valor_atual or valor_atual[-1] in ['+', '-']:
                return
        if tecla.isdigit() and valor_atual == "Expressão Inválida!":
            valor_atual = ""
        self.valor_campo_expressao.set(valor_atual + tecla)

    def _limpar_expressao(self):
        self.valor_campo_expressao.set("")

    def _processar_expressao(self):
        expressao = self.valor_campo_expressao.get()
        if not expressao:
            messagebox.showwarning("Expressão Vazia", "Digite uma expressão para gerar código.")
            return

        componentes = re.findall(r'(\d+)|([+-])', expressao)

        numeros = []
        operadores = []

        try:
            num_atual = ""
            for parte_num, parte_op in componentes:
                if parte_num:
                    num_atual += parte_num
                elif parte_op:
                    if num_atual:
                        numeros.append(int(num_atual))
                        num_atual = ""
                    operadores.append(parte_op)

            if num_atual:
                numeros.append(int(num_atual))

            if not numeros:
                raise ValueError("Nenhum número válido encontrado.")

            if len(operadores) >= len(numeros):
                 raise ValueError("Expressão mal formada (operador sem operando).")

            codigo = "; Código gerado para: " + expressao + "\n"
            codigo += "; Dados armazenados no final da memória.\n\n"

            inicio_dados = CAPACIDADE_MEMORIA - len(numeros)
            if inicio_dados < 0:
                raise ValueError(f"Expressão muito longa. Máximo de {CAPACIDADE_MEMORIA} números na memória.")

            codigo += f"CAR {inicio_dados:01X}   ; Carrega o primeiro número no ACC\n"

            for i in range(len(operadores)):
                op = operadores[i]
                endereco = inicio_dados + i + 1
                if op == "+":
                    codigo += f"SOM {endereco:01X}   ; Soma o próximo número\n"
                elif op == "-":
                    codigo += f"SUB {endereco:01X}   ; Subtrai o próximo número\n"

            codigo += "SAI      ; Mostra o resultado final\n"
            codigo += "PAR      ; Termina a execução\n\n"

            codigo += f"ORG {inicio_dados:01X}   ; Seção de dados\n"
            for num in numeros:
                if not (0 <= num <= 255):
                    raise ValueError(f"Número '{num}' fora do intervalo (0-255).")
                codigo += f"DB {num}     ; Byte de dados\n"

            self.area_texto.delete(1.0, tk.END)
            self.area_texto.insert(1.0, codigo)
            self.mensagem_status.set("Código gerado. Clique em 'Montar Programa'.")
            self.valor_campo_expressao.set(expressao)

            if not self._montar_codigo():
                 self.area_texto.delete(1.0, tk.END)
                 self.mensagem_status.set("Erro durante a montagem.")
                 self.valor_campo_expressao.set("Expressão Inválida!")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao processar expressão: {str(e)}")
            self.mensagem_status.set(f"Erro: {str(e)}")
            self.valor_campo_expressao.set("Expressão Inválida!")

    def reiniciar_simulador(self):
        self.executando = False
        self.nucleo.registradores = {
            "ContadorPrograma": 0,
            "Acumulador": 0,
            "RegistradorEndereco": 0,
            "RegistradorInstrucao": 0,
            "RegistradorB": 0,
            "RegistradorSaida": 0,
            "Flags": {"Zero": 0, "Carry": 0}
        }
        self.nucleo.memoria_principal = [0] * CAPACIDADE_MEMORIA

        self._atualizar_tela()
        self.linha_codigo_atual = -1
        self.mensagem_status.set("Simulador reiniciado. Carregue e monte um programa.")
        self._limpar_destaques()
        self.canvas_cpu.itemconfig("bloco_ula_val", text="")
        for i in range(CAPACIDADE_MEMORIA):
            self.canvas_cpu.itemconfig(f"celula_ram_{i}", fill="#34495e")
            self.canvas_cpu.itemconfig(f"endereco_ram_{i}", fill="#bdc3c7")

    def _atualizar_tela(self):
        regs = self.nucleo.registradores
        self.canvas_cpu.itemconfig("bloco_cp_val", text=f"0x{regs['ContadorPrograma']:01X}")
        self.canvas_cpu.itemconfig("bloco_rem_val", text=f"0x{regs['RegistradorEndereco']:01X}")
        self.canvas_cpu.itemconfig("bloco_ri_val", text=f"0x{regs['RegistradorInstrucao']:02X}")
        self.canvas_cpu.itemconfig("bloco_acc_val", text=f"0x{regs['Acumulador']:02X}")
        self.canvas_cpu.itemconfig("bloco_regb_val", text=f"0x{regs['RegistradorB']:02X}")
        self.canvas_cpu.itemconfig("bloco_saida_val", text=f"0x{regs['RegistradorSaida']:02X}")

        for i in range(CAPACIDADE_MEMORIA):
            self.canvas_cpu.itemconfig(f"valor_ram_{i}", text=f"{self.nucleo.memoria_principal[i]:02X}")

        for i in range(CAPACIDADE_MEMORIA):
            self.canvas_cpu.itemconfig(f"celula_ram_{i}", fill="#34495e")
            self.canvas_cpu.itemconfig(f"endereco_ram_{i}", fill="#bdc3c7")

        if 0 <= regs['RegistradorEndereco'] < CAPACIDADE_MEMORIA:
            self.canvas_cpu.itemconfig(f"celula_ram_{regs['RegistradorEndereco']}", fill="#9b59b6")
            self.canvas_cpu.itemconfig(f"endereco_ram_{regs['RegistradorEndereco']}", fill="#ffffff")

        saida = regs['RegistradorSaida']
        for i in range(8):
            if (saida >> i) & 1:
                self.canvas_cpu.itemconfig(self.leds_saida[7-i], fill="#e74c3c")
            else:
                self.canvas_cpu.itemconfig(self.leds_saida[7-i], fill="#34495e")

    def _animar_transferencia(self, origem, destino, duracao=0.3):
        cor_ativa = "#e74c3c"  # Vermelho para animação
        cor_barramento = "#8e44ad"  # Roxo escuro
        cor_componente = "#2c3e50"  # Azul escuro

        tag_origem = f"{origem[:-6]}_conexao" if origem.endswith("_bloco") else f"{origem}_conexao"
        tag_destino = f"{destino[:-6]}_conexao" if destino.endswith("_bloco") else f"{destino}_conexao"

        if origem == "ram": tag_origem = "conexao_ram"
        if destino == "ram": tag_destino = "conexao_ram"
        if origem == "bloco_saida": tag_origem = "conexao_saida"
        if destino == "bloco_saida": tag_destino = "conexao_saida"
        if origem == "bloco_ula": tag_origem = "conexao_ula"
        if destino == "bloco_ula": tag_destino = "conexao_ula"

        self.canvas_cpu.itemconfig(origem, fill=cor_ativa)
        if tag_origem and self.canvas_cpu.find_withtag(tag_origem):
            self.canvas_cpu.itemconfig(tag_origem, fill=cor_ativa, width=2)
        self.canvas_cpu.update()
        time.sleep(duracao / (3 * self.velocidade_simulacao))

        self.canvas_cpu.itemconfig("barramento", fill=cor_ativa, width=4)
        self.canvas_cpu.update()
        time.sleep(duracao / (3 * self.velocidade_simulacao))

        if tag_destino and self.canvas_cpu.find_withtag(tag_destino):
            self.canvas_cpu.itemconfig(tag_destino, fill=cor_ativa, width=2)
        self.canvas_cpu.itemconfig(destino, fill=cor_ativa)
        self.canvas_cpu.update()
        time.sleep(duracao / (3 * self.velocidade_simulacao))

        self.canvas_cpu.itemconfig(origem, fill=cor_componente)
        if tag_origem and self.canvas_cpu.find_withtag(tag_origem):
            self.canvas_cpu.itemconfig(tag_origem, fill=cor_barramento, width=1)
        self.canvas_cpu.itemconfig("barramento", fill=cor_barramento, width=3)
        if tag_destino and self.canvas_cpu.find_withtag(tag_destino):
            self.canvas_cpu.itemconfig(tag_destino, fill=cor_barramento, width=1)
        self.canvas_cpu.itemconfig(destino, fill=cor_componente)
        self.canvas_cpu.update()
        time.sleep(0.1 / self.velocidade_simulacao)

    def _animar_conexao_direta(self, origem, destino, linha, duracao=0.3):
        cor_ativa = "#e74c3c"
        cor_barramento = "#8e44ad"
        cor_componente = "#2c3e50"

        self.canvas_cpu.itemconfig(origem, fill=cor_ativa)
        self.canvas_cpu.itemconfig(linha, fill=cor_ativa, width=2)
        self.canvas_cpu.itemconfig(destino, fill=cor_ativa)
        self.canvas_cpu.update()
        time.sleep(duracao / self.velocidade_simulacao)

        self.canvas_cpu.itemconfig(origem, fill=cor_componente)
        self.canvas_cpu.itemconfig(linha, fill=cor_barramento, width=1)
        self.canvas_cpu.itemconfig(destino, fill=cor_componente)
        self.canvas_cpu.update()
        time.sleep(0.1 / self.velocidade_simulacao)

    def _piscar_relogio(self):
        for _ in range(2):
            self.canvas_cpu.itemconfig("relogio", fill="#e74c3c")
            self.canvas_cpu.update()
            time.sleep(0.15 / self.velocidade_simulacao)
            self.canvas_cpu.itemconfig("relogio", fill="#2c3e50")
            self.canvas_cpu.update()
            time.sleep(0.15 / self.velocidade_simulacao)

    def _destacar_componente(self, componente, duracao=0.5):
        cor_original = "#2c3e50"
        self.canvas_cpu.itemconfig(componente, fill="#e74c3c")
        tag_valor = f"{componente}_val"
        try:
             self.canvas_cpu.itemconfig(tag_valor, fill="white")
        except:
             pass

        self.canvas_cpu.update()
        time.sleep(duracao / self.velocidade_simulacao)

        self.canvas_cpu.itemconfig(componente, fill=cor_original)
        try:
            self.canvas_cpu.itemconfig(tag_valor, fill="white")
        except:
            pass
        self.canvas_cpu.update()

    def _destacar_linha(self, linha):
        if self.linha_codigo_atual != -1:
            self.area_texto.tag_remove("linha_ativa", f"{self.linha_codigo_atual}.0", f"{self.linha_codigo_atual}.end")

        self.area_texto.tag_add("linha_ativa", f"{linha}.0", f"{linha}.end")
        self.linha_codigo_atual = linha
        self.area_texto.see(f"{linha}.0")

    def _limpar_destaques(self):
        if self.linha_codigo_atual != -1:
            self.area_texto.tag_remove("linha_ativa", f"{self.linha_codigo_atual}.0", f"{self.linha_codigo_atual}.end")
            self.linha_codigo_atual = -1
        self.area_texto.tag_remove("erro", "1.0", tk.END)


    def _montar_codigo(self):
        codigo = self.area_texto.get(1.0, tk.END)
        linhas = codigo.split('\n')

        memoria = [0] * CAPACIDADE_MEMORIA

        ponteiro_instrucao = 0
        ponteiro_dados = None

        self.area_texto.tag_remove("erro", "1.0", tk.END)

        try:
            for num_linha, linha in enumerate(linhas, 1):
                linha_processada = linha
                inicio_comentario = linha_processada.find(';')
                if inicio_comentario != -1:
                    linha_processada = linha_processada[:inicio_comentario].strip()

                if not linha_processada:
                    continue

                partes = linha_processada.split()
                mnemonic = partes[0].upper()

                if mnemonic == "ORG":
                    if len(partes) < 2:
                        raise ValueError(f"ORG requer um endereço.")
                    endereco = int(partes[1], 16)
                    if not (0 <= endereco < CAPACIDADE_MEMORIA):
                        raise ValueError(f"Endereço ORG fora do intervalo (00-{CAPACIDADE_MEMORIA-1:01X}).")
                    ponteiro_dados = endereco
                    continue

                elif mnemonic == "DB":
                    if ponteiro_dados is None:
                        raise ValueError(f"DB deve ser precedido por ORG.")
                    if len(partes) < 2:
                        raise ValueError(f"DB requer um valor.")

                    valor = int(partes[1])
                    if not (0 <= valor <= 255):
                        raise ValueError(f"Valor DB deve estar entre 0 e 255.")

                    if ponteiro_dados >= CAPACIDADE_MEMORIA:
                        raise ValueError(f"Memória insuficiente para DB (máx {CAPACIDADE_MEMORIA} bytes).")

                    memoria[ponteiro_dados] = valor
                    ponteiro_dados += 1
                    continue

                if ponteiro_instrucao >= CAPACIDADE_MEMORIA:
                    raise ValueError(f"Programa muito grande para memória (máx {CAPACIDADE_MEMORIA} bytes).")

                opcode = {
                    "CAR": 0b0000,
                    "SOM": 0b0001,
                    "SUB": 0b0010,
                    "SAI": 0b1110,
                    "PAR": 0b1111
                }.get(mnemonic)

                if opcode is None:
                    raise ValueError(f"Mnemonico inválido: {mnemonic}.")

                operando = 0
                if mnemonic in ["CAR", "SOM", "SUB"]:
                    if len(partes) < 2:
                        raise ValueError(f"Operando faltando para {mnemonic}.")
                    try:
                        operando = int(partes[1], 16)
                    except ValueError:
                        raise ValueError(f"Operando inválido para {mnemonic}. Esperado endereço hexadecimal.")

                    if not (0 <= operando < CAPACIDADE_MEMORIA):
                        raise ValueError(f"Operando para {mnemonic} deve estar entre 00 e {CAPACIDADE_MEMORIA-1:01X}.")
                elif len(partes) > 1:
                     raise ValueError(f"Instrução {mnemonic} não aceita operando.")

                memoria[ponteiro_instrucao] = (opcode << 4) | operando
                ponteiro_instrucao += 1

            self.nucleo.memoria_principal = memoria
            self.nucleo.registradores['ContadorPrograma'] = 0
            self._atualizar_tela()
            self.mensagem_status.set("Montagem concluída! Pronto para executar.")
            self._limpar_destaques()
            return True

        except Exception as e:
            self.area_texto.tag_add("erro", f"{num_linha}.0", f"{num_linha}.end")
            messagebox.showerror("Erro", f"Erro na linha {num_linha}: {str(e)}")
            self.mensagem_status.set(f"Erro na linha {num_linha}.")
            return False

    def _iniciar_simulacao(self):
        if self.executando:
            return

        self.nucleo.registradores['ContadorPrograma'] = 0
        self._atualizar_tela()
        self._limpar_destaques()

        def executar_simulacao():
            self.executando = True
            self.mensagem_status.set("Executando programa...")

            while self.executando and self.nucleo.registradores['ContadorPrograma'] < CAPACIDADE_MEMORIA:
                linha_asm = 1
                contador_instrucoes = 0
                for i, linha in enumerate(self.area_texto.get("1.0", tk.END).split('\n')):
                    linha_limpa = linha.strip()
                    if linha_limpa and not linha_limpa.startswith(';'):
                        if contador_instrucoes == self.nucleo.registradores['ContadorPrograma']:
                            self._destacar_linha(i + 1)
                            break
                        contador_instrucoes += 1
                    linha_asm += 1

                if not self._executar_passo():
                    break
                time.sleep(0.5 / self.velocidade_simulacao)

            self.executando = False
            self._limpar_destaques()
            if self.nucleo.registradores['ContadorPrograma'] >= CAPACIDADE_MEMORIA:
                self.mensagem_status.set("Execução finalizada (Contador de Programa excedeu memória).")
            else:
                self.mensagem_status.set("Execução finalizada (Instrução PAR encontrada).")

        import threading
        thread = threading.Thread(target=executar_simulacao)
        thread.start()

    def _executar_passo(self):
        if self.nucleo.registradores['ContadorPrograma'] >= CAPACIDADE_MEMORIA:
            self.mensagem_status.set("Contador de Programa além do limite. Reinicie.")
            self.executando = False
            self._limpar_destaques()
            return False

        linha_editor = 1
        instrucoes_executadas = 0
        for i, linha in enumerate(self.area_texto.get("1.0", tk.END).split('\n')):
            linha_limpa = linha.strip()
            if linha_limpa and not linha_limpa.startswith(';'):
                if instrucoes_executadas == self.nucleo.registradores['ContadorPrograma']:
                    self._destacar_linha(i + 1)
                    break
                instrucoes_executadas += 1
            linha_editor += 1

        self._piscar_relogio()

        # 1. CICLO DE BUSCA
        self.mensagem_status.set(f"Busca (T1): CP ({self.nucleo.registradores['ContadorPrograma']:01X}) para REM")
        self._animar_transferencia("bloco_cp", "bloco_rem")
        self.nucleo.registradores['RegistradorEndereco'] = self.nucleo.registradores['ContadorPrograma']
        self._atualizar_tela()
        time.sleep(0.4 / self.velocidade_simulacao)

        self.mensagem_status.set(f"Busca (T2): Incrementar CP ({self.nucleo.registradores['ContadorPrograma']:01X} -> {self.nucleo.registradores['ContadorPrograma']+1:01X})")
        self._destacar_componente("bloco_cp")
        self.nucleo.registradores['ContadorPrograma'] += 1
        self._atualizar_tela()
        time.sleep(0.4 / self.velocidade_simulacao)

        self.mensagem_status.set(f"Busca (T3): Memória[{self.nucleo.registradores['RegistradorEndereco']:01X}] para RI")
        if 0 <= self.nucleo.registradores['RegistradorEndereco'] < CAPACIDADE_MEMORIA:
            self.canvas_cpu.itemconfig(f"celula_ram_{self.nucleo.registradores['RegistradorEndereco']}", fill="#e74c3c")
            self.canvas_cpu.update()
            time.sleep(0.2 / self.velocidade_simulacao)
            self._animar_transferencia("ram", "bloco_ri")
            self.canvas_cpu.itemconfig(f"celula_ram_{self.nucleo.registradores['RegistradorEndereco']}", fill="#9b59b6")

        self.nucleo.registradores['RegistradorInstrucao'] = self.nucleo.memoria_principal[self.nucleo.registradores['RegistradorEndereco']]
        self._atualizar_tela()
        time.sleep(0.4 / self.velocidade_simulacao)

        # 2. CICLO DE EXECUÇÃO
        opcode = self.nucleo.registradores['RegistradorInstrucao'] >> 4
        operando = self.nucleo.registradores['RegistradorInstrucao'] & 0x0F

        if opcode in self.nucleo.conjunto_instrucoes:
            nome_instrucao, funcao = self.nucleo.conjunto_instrucoes[opcode]
            self.mensagem_status.set(f"Executando: {nome_instrucao} 0x{operando:01X}")

            parar = funcao(operando)
            self._atualizar_tela()
            self.canvas_cpu.itemconfig("bloco_ula_val", text="")
            return not parar
        else:
            messagebox.showerror("Erro", f"Opcode inválido: {opcode:04b} na instrução 0x{self.nucleo.registradores['RegistradorInstrucao']:02X} no endereço 0x{self.nucleo.registradores['RegistradorEndereco']:01X}.")
            self.executando = False
            self._limpar_destaques()
            return False

    def _executar_car(self, operando):
        self.mensagem_status.set(f"Execução CAR: Carregar Mem[{operando:01X}] no ACC")
        self._destacar_componente("bloco_ri")
        self._animar_transferencia("bloco_ri", "bloco_rem")
        self.nucleo.registradores['RegistradorEndereco'] = operando
        self._atualizar_tela()
        time.sleep(0.4 / self.velocidade_simulacao)

        self.mensagem_status.set(f"Execução CAR: Memória[{self.nucleo.registradores['RegistradorEndereco']:01X}] para ACC")
        if 0 <= self.nucleo.registradores['RegistradorEndereco'] < CAPACIDADE_MEMORIA:
            self.canvas_cpu.itemconfig(f"celula_ram_{self.nucleo.registradores['RegistradorEndereco']}", fill="#e74c3c")
            self.canvas_cpu.update()
            time.sleep(0.2 / self.velocidade_simulacao)
            self._animar_transferencia("ram", "bloco_acc")
            self.canvas_cpu.itemconfig(f"celula_ram_{self.nucleo.registradores['RegistradorEndereco']}", fill="#9b59b6")

        self.nucleo.registradores['Acumulador'] = self.nucleo.memoria_principal[self.nucleo.registradores['RegistradorEndereco']]
        self._atualizar_tela()
        time.sleep(0.4 / self.velocidade_simulacao)

        return False

    def _executar_som(self, operando):
        self.mensagem_status.set(f"Execução SOM: Somar Mem[{operando:01X}] ao ACC")
        self._destacar_componente("bloco_ri")
        self._animar_transferencia("bloco_ri", "bloco_rem")
        self.nucleo.registradores['RegistradorEndereco'] = operando
        self._atualizar_tela()
        time.sleep(0.4 / self.velocidade_simulacao)

        self.mensagem_status.set(f"Execução SOM: Memória[{self.nucleo.registradores['RegistradorEndereco']:01X}] para Reg B")
        if 0 <= self.nucleo.registradores['RegistradorEndereco'] < CAPACIDADE_MEMORIA:
            self.canvas_cpu.itemconfig(f"celula_ram_{self.nucleo.registradores['RegistradorEndereco']}", fill="#e74c3c")
            self.canvas_cpu.update()
            time.sleep(0.2 / self.velocidade_simulacao)
            self._animar_transferencia("ram", "bloco_regb")
            self.canvas_cpu.itemconfig(f"celula_ram_{self.nucleo.registradores['RegistradorEndereco']}", fill="#9b59b6")
        self.nucleo.registradores['RegistradorB'] = self.nucleo.memoria_principal[self.nucleo.registradores['RegistradorEndereco']]
        self._atualizar_tela()
        time.sleep(0.4 / self.velocidade_simulacao)

        self.mensagem_status.set("Execução SOM: ACC + Reg B -> ULA -> ACC")
        self._animar_conexao_direta("bloco_acc", "bloco_ula", "conexao_acc_alu")
        self._animar_conexao_direta("bloco_regb", "bloco_ula", "conexao_regb_alu")

        resultado = (self.nucleo.registradores['Acumulador'] + self.nucleo.registradores['RegistradorB']) & 0xFF
        self.canvas_cpu.itemconfig("bloco_ula_val", text=f"0x{resultado:02X}", font=('Consolas', 11))
        self._destacar_componente("bloco_ula")
        self._animar_transferencia("bloco_ula", "bloco_acc")

        self.nucleo.registradores['Acumulador'] = resultado
        self._atualizar_tela()
        time.sleep(0.4 / self.velocidade_simulacao)

        return False

    def _executar_sub(self, operando):
        self.mensagem_status.set(f"Execução SUB: Subtrair Mem[{operando:01X}] do ACC")
        self._destacar_componente("bloco_ri")
        self._animar_transferencia("bloco_ri", "bloco_rem")
        self.nucleo.registradores['RegistradorEndereco'] = operando
        self._atualizar_tela()
        time.sleep(0.4 / self.velocidade_simulacao)

        self.mensagem_status.set(f"Execução SUB: Memória[{self.nucleo.registradores['RegistradorEndereco']:01X}] para Reg B")
        if 0 <= self.nucleo.registradores['RegistradorEndereco'] < CAPACIDADE_MEMORIA:
            self.canvas_cpu.itemconfig(f"celula_ram_{self.nucleo.registradores['RegistradorEndereco']}", fill="#e74c3c")
            self.canvas_cpu.update()
            time.sleep(0.2 / self.velocidade_simulacao)
            self._animar_transferencia("ram", "bloco_regb")
            self.canvas_cpu.itemconfig(f"celula_ram_{self.nucleo.registradores['RegistradorEndereco']}", fill="#9b59b6")
        self.nucleo.registradores['RegistradorB'] = self.nucleo.memoria_principal[self.nucleo.registradores['RegistradorEndereco']]
        self._atualizar_tela()
        time.sleep(0.4 / self.velocidade_simulacao)

        self.mensagem_status.set("Execução SUB: ACC - Reg B -> ULA -> ACC")
        self._animar_conexao_direta("bloco_acc", "bloco_ula", "conexao_acc_alu")
        self._animar_conexao_direta("bloco_regb", "bloco_ula", "conexao_regb_alu")

        resultado = (self.nucleo.registradores['Acumulador'] - self.nucleo.registradores['RegistradorB']) & 0xFF
        self.canvas_cpu.itemconfig("bloco_ula_val", text=f"0x{resultado:02X}", font=('Consolas', 11))
        self._destacar_componente("bloco_ula")
        self._animar_transferencia("bloco_ula", "bloco_acc")

        self.nucleo.registradores['Acumulador'] = resultado
        self._atualizar_tela()
        time.sleep(0.4 / self.velocidade_simulacao)

        return False

    def _executar_sai(self, _):
        self.mensagem_status.set("Execução SAI: ACC para Registrador de Saída")
        self._destacar_componente("bloco_acc")
        self._animar_transferencia("bloco_acc", "bloco_saida")

        self.nucleo.registradores['RegistradorSaida'] = self.nucleo.registradores['Acumulador']
        self._atualizar_tela()
        time.sleep(0.4 / self.velocidade_simulacao)

        return False

    def _executar_par(self, _):
        self.mensagem_status.set("Execução parada (instrução PAR encontrada).")
        self._destacar_componente("bloco_ri")
        self.executando = False
        return True

    def _atualizar_velocidade(self, valor):
        self.velocidade_simulacao = float(valor)

if __name__ == "__main__":
    janela = tk.Tk()
    app = AplicativoSimulador(janela)
    janela.mainloop()