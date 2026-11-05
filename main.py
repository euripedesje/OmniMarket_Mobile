import flet as ft
import requests
import random
import threading
import traceback
import urllib.parse
from datetime import datetime, timezone, timedelta
import os

# =========================================================================
# CLOUD CREDENTIALS & TIMEZONE (OMNIMARKET POS) - CHAVES OFICIAIS BAZAR ANNY
# =========================================================================
URL = "https://skqjtjpbjbkkxgsvppao.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNrcWp0anBiamJra3hnc3ZwcGFvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTMxOTYyMzEsImV4cCI6MjEwODc3MjIzMX0.PNJpq3nFKj4WiBf34rF9MlU2I6SzDYEh3yrYLvttp3k"
FUSO_BR = timezone(timedelta(hours=-3))

HEADERS = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# =========================================================================
# TECH CORPORATE PALETTE
# =========================================================================
COR_FUNDO = "#F0F4F8"           
COR_PAINEL = "#FFFFFF"          
COR_TEXTO = "#102A43"           
COR_DESTAQUE = "#334E68"        
COR_BOTAO_PRINCIPAL = "#0B3954" 
COR_VERDE_SUCESSO = "#27AE60"   
COR_VERMELHO_ERRO = "#C0392B"   

def main(page: ft.Page):
    try:
        page.title = "OmniMarket POS"
        page.window_width = 420
        page.window_height = 800
        page.theme_mode = ft.ThemeMode.LIGHT
        page.bgcolor = COR_FUNDO
        page.padding = 0
        
        page.window_icon = "icon.png"

        def mostrar_mensagem(texto, cor):
            page.snack_bar = ft.SnackBar(ft.Text(texto, size=16, color="white"), bgcolor=cor)
            page.snack_bar.open = True
            page.update()

        # =====================================================================
        # COMPONENTE DE BOTÃO BLINDADO (À prova de erros do Flet 1.0)
        # =====================================================================
        def botao_customizado(texto, cor_bg, acao, expandir=False, altura=45, largura=None):
            return ft.Container(
                content=ft.Text(texto, color="white", weight=ft.FontWeight.BOLD, size=16),
                bgcolor=cor_bg,
                padding=10,
                border_radius=8,
                alignment=ft.Alignment(0, 0),
                on_click=acao,
                expand=expandir,
                height=altura,
                width=largura
            )

        # =====================================================================
        # TOP HEADER WITH BANNER
        # =====================================================================
        topo_app = ft.Container(
            content=ft.Text("OmniMarket POS", size=24, weight=ft.FontWeight.BOLD, color="white"),
            bgcolor=COR_BOTAO_PRINCIPAL,
            padding=20,
            alignment=ft.Alignment(0, 0),
            width=float('inf')
        )
        
        if os.path.exists("assets/banner.png"):
            topo_app = ft.Container(
                content=ft.Image(src="banner.png", height=60),
                bgcolor=COR_BOTAO_PRINCIPAL, padding=10, alignment=ft.Alignment(0, 0), width=float('inf')
            )

        # =====================================================================
        # BARCODE SCANNER SYSTEM
        # =====================================================================
        def abrir_leitor_codigo(campo_destino, ao_ler_callback=None):
            input_manual = ft.TextField(
                label="Código manual", autofocus=True,
                keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_DESTAQUE,
                on_submit=lambda e: confirmar_codigo(e.control.value)
            )

            def confirmar_codigo(valor):
                if valor and str(valor).strip():
                    codigo_final = str(valor).strip()
                    campo_destino.value = codigo_final
                    dialog_camera.open = False
                    page.update()
                    mostrar_mensagem(f"Código: {codigo_final}", COR_VERDE_SUCESSO)
                    if ao_ler_callback: ao_ler_callback(codigo_final)

            def colar_da_area_transferencia(e):
                try:
                    texto_colado = page.get_clipboard()
                    if texto_colado and str(texto_colado).strip(): confirmar_codigo(texto_colado)
                    else: mostrar_mensagem("Área de transferência vazia!", COR_VERMELHO_ERRO)
                except Exception: mostrar_mensagem("Cole manualmente.", COR_DESTAQUE)

            def abrir_camera_externa(e): page.launch_url("https://scanapp.org/")
            def fechar_dialog(e=None):
                dialog_camera.open = False
                page.update()

            dialog_camera = ft.AlertDialog(
                modal=True,
                title=ft.Text("📷 Ler Código", size=18, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
                content=ft.Container(
                    width=310,
                    content=ft.Column([
                        botao_customizado("📷 ABRIR CÂMERA", COR_BOTAO_PRINCIPAL, abrir_camera_externa, largura=300),
                        botao_customizado("📋 COLAR CÓDIGO", COR_DESTAQUE, colar_da_area_transferencia, largura=300),
                        ft.Divider(), input_manual,
                    ], spacing=10, tight=True)
                ),
                actions=[
                    ft.Container(content=ft.Text("Cancelar", color="gray", weight=ft.FontWeight.BOLD), on_click=fechar_dialog, padding=10),
                    botao_customizado("Confirmar", COR_VERDE_SUCESSO, lambda e: confirmar_codigo(input_manual.value))
                ]
            )
            page.dialog = dialog_camera
            dialog_camera.open = True
            page.update()

        # =====================================================================
        # TAB 1: INVENTORY CHECK
        # =====================================================================
        lista_produtos = ft.ListView(expand=True, spacing=10, padding=10)
        busca_input = ft.TextField(
            label="🔍 Buscar nome ou código", expand=True, border_color=COR_DESTAQUE, 
            focused_border_color=COR_BOTAO_PRINCIPAL, on_submit=lambda e: threading.Thread(target=carregar_estoque, args=(e.control.value,)).start()
        )

        def carregar_estoque(termo=""):
            lista_produtos.controls.clear()
            lista_produtos.controls.append(ft.Text("Sincronizando...", color="gray", text_align=ft.TextAlign.CENTER))
            page.update()
            try:
                termo_limpo = str(termo).strip() if termo else ""
                if termo_limpo:
                    if termo_limpo.isdigit(): resp = requests.get(f"{URL}/rest/v1/produtos?codigo=eq.{termo_limpo}&select=*", headers=HEADERS, timeout=8)
                    else:
                        termo_url = urllib.parse.quote(termo_limpo)
                        resp = requests.get(f"{URL}/rest/v1/produtos?nome=ilike.*{termo_url}*&select=*", headers=HEADERS, timeout=8)
                else: resp = requests.get(f"{URL}/rest/v1/produtos?order=pid.desc&limit=30&select=*", headers=HEADERS, timeout=8)
                    
                produtos = resp.json()
                lista_produtos.controls.clear()
                
                if not produtos: lista_produtos.controls.append(ft.Text("Nenhum produto encontrado.", size=16, text_align=ft.TextAlign.CENTER))
                else:
                    for p in produtos:
                        estoque_atual = p.get('estoque', 0)
                        lista_produtos.controls.append(
                            ft.Card(
                                elevation=2, color=COR_PAINEL,
                                content=ft.Container(
                                    padding=15,
                                    content=ft.Column([
                                        ft.Text(p.get('nome', 'Sem Nome'), weight=ft.FontWeight.BOLD, size=18, color=COR_TEXTO),
                                        ft.Row([
                                            ft.Text(f"SKU: {p.get('codigo', '')}", color="gray", size=14),
                                            ft.Text(f"Estoque: {estoque_atual}", color=COR_VERMELHO_ERRO if estoque_atual <= 2 else COR_VERDE_SUCESSO, weight=ft.FontWeight.BOLD, size=14)
                                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                        ft.Text(f"R$ {float(p.get('preco', 0.0)):.2f}", size=20, color=COR_DESTAQUE, weight=ft.FontWeight.BOLD)
                                    ])
                                )
                            )
                        )
            except Exception:
                lista_produtos.controls.clear()
                lista_produtos.controls.append(ft.Text("Erro de conexão.", color=COR_VERMELHO_ERRO, text_align=ft.TextAlign.CENTER))
            page.update()

        view_estoque = ft.Column([
            topo_app,
            ft.Container(
                content=ft.Row([
                    busca_input,
                    botao_customizado("📷", COR_BOTAO_PRINCIPAL, lambda e: abrir_leitor_codigo(busca_input, ao_ler_callback=lambda cod: threading.Thread(target=carregar_estoque, args=(cod,)).start())),
                    botao_customizado("🔍", COR_DESTAQUE, lambda e: threading.Thread(target=carregar_estoque, args=(busca_input.value,)).start())
                ]), padding=10
            ), lista_produtos
        ], expand=True, spacing=0, visible=True)

        # =====================================================================
        # TAB 2: MOBILE POS (CART, SEARCH, CUSTOM ITEM)
        # =====================================================================
        carrinho_mobile = []
        produto_atual_venda = {"codigo": "", "nome": "", "preco": 0.0, "custo": 0.0, "estoque": 0}
        
        venda_cod_input = ft.TextField(label="Código de Barras", border_color=COR_DESTAQUE, expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        venda_qtd_input = ft.TextField(label="Qtd", value="1", width=60, keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_DESTAQUE, text_align=ft.TextAlign.CENTER)
        
        lbl_venda_nome = ft.Text("Nenhum produto...", size=16, weight=ft.FontWeight.BOLD, color=COR_TEXTO, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1)
        lbl_venda_info = ft.Text("Aguardando código ou busca.", size=13, color="gray")
        
        lista_carrinho = ft.ListView(expand=True, spacing=5)
        lbl_total_carrinho = ft.Text("R$ 0.00", size=26, weight=ft.FontWeight.BOLD, color=COR_VERDE_SUCESSO)
        
        combo_pagamento = ft.Dropdown(
            options=[ft.dropdown.Option("Dinheiro"), ft.dropdown.Option("PIX"), ft.dropdown.Option("Cartão Crédito"), ft.dropdown.Option("Cartão Débito"), ft.dropdown.Option("Fiado")],
            value="Dinheiro", border_color=COR_DESTAQUE, expand=True, height=50
        )

        def atualizar_ui_carrinho():
            lista_carrinho.controls.clear()
            total_venda = 0.0
            if not carrinho_mobile: lista_carrinho.controls.append(ft.Text("Carrinho vazio.", color="gray", text_align=ft.TextAlign.CENTER))
            else:
                for idx, item in enumerate(carrinho_mobile):
                    total_venda += item['subtotal']
                    lista_carrinho.controls.append(
                        ft.Card(
                            elevation=1, color=COR_PAINEL,
                            content=ft.ListTile(
                                title=ft.Text(f"{item['qtd']}x {item['nome']}", weight=ft.FontWeight.BOLD, size=14),
                                subtitle=ft.Text(f"R$ {item['preco']:.2f} un | Sub: R$ {item['subtotal']:.2f}", size=13),
                                trailing=ft.Container(content=ft.Text("❌", size=18, color=COR_VERMELHO_ERRO), on_click=lambda e, i=idx: remover_do_carrinho(i), padding=5)
                            )
                        )
                    )
            lbl_total_carrinho.value = f"R$ {total_venda:.2f}"
            page.update()

        def remover_do_carrinho(index):
            if 0 <= index < len(carrinho_mobile):
                removido = carrinho_mobile.pop(index)
                mostrar_mensagem(f"Removido: {removido['nome']}", COR_DESTAQUE)
                atualizar_ui_carrinho()

        def cancelar_venda(e=None):
            carrinho_mobile.clear()
            produto_atual_venda["codigo"] = ""
            venda_cod_input.value = ""
            venda_qtd_input.value = "1"
            lbl_venda_nome.value = "Nenhum produto..."
            lbl_venda_info.value = "Aguardando código ou busca."
            combo_pagamento.value = "Dinheiro"
            atualizar_ui_carrinho()
            mostrar_mensagem("Venda cancelada.", COR_VERMELHO_ERRO)

        def processar_leitura_venda(codigo):
            cod_limpo = str(codigo).strip()
            if not cod_limpo: return
            lbl_venda_nome.value = "Buscando..."
            lbl_venda_info.value = ""
            page.update()
            
            def buscar():
                try:
                    cod_url = urllib.parse.quote(cod_limpo)
                    resp = requests.get(f"{URL}/rest/v1/produtos?codigo=eq.{cod_url}&select=*", headers=HEADERS, timeout=5)
                    produtos = resp.json()
                    
                    if produtos and len(produtos) > 0:
                        p = produtos[0]
                        produto_atual_venda["codigo"] = p.get('codigo', '')
                        produto_atual_venda["nome"] = p.get('nome', '')
                        produto_atual_venda["preco"] = float(p.get('preco', 0.0))
                        produto_atual_venda["custo"] = float(p.get('custo', 0.0))
                        produto_atual_venda["estoque"] = int(p.get('estoque', 0))
                        lbl_venda_nome.value = produto_atual_venda["nome"]
                        lbl_venda_info.value = f"R$ {produto_atual_venda['preco']:.2f} | Estoque: {produto_atual_venda['estoque']}"
                        mostrar_mensagem("Pronto para adicionar!", COR_BOTAO_PRINCIPAL)
                    else:
                        lbl_venda_nome.value = "Não cadastrado!"
                        lbl_venda_info.value = "Verifique o código."
                        produto_atual_venda["codigo"] = ""
                    page.update()
                except Exception:
                    lbl_venda_nome.value = "Erro de Rede"
                    page.update()
            threading.Thread(target=buscar).start()

        venda_cod_input.on_submit = lambda e: processar_leitura_venda(e.control.value)

        def adicionar_ao_carrinho(e):
            if not produto_atual_venda["codigo"]: return mostrar_mensagem("Busque um item primeiro!", COR_VERMELHO_ERRO)
            try:
                qtd = int(venda_qtd_input.value)
                if qtd <= 0: raise ValueError
            except: return mostrar_mensagem("Quantidade inválida!", COR_VERMELHO_ERRO)
            
            qtd_ja_no_carrinho = sum(i['qtd'] for i in carrinho_mobile if i['codigo'] == produto_atual_venda["codigo"])
            if (qtd + qtd_ja_no_carrinho) > produto_atual_venda["estoque"]:
                return mostrar_mensagem(f"Estoque insuficiente! (Disp: {produto_atual_venda['estoque']})", COR_VERMELHO_ERRO)
                
            subtotal = produto_atual_venda["preco"] * qtd
            item_existente = next((i for i in carrinho_mobile if i['codigo'] == produto_atual_venda["codigo"]), None)
            
            if item_existente:
                item_existente['qtd'] += qtd
                item_existente['subtotal'] += subtotal
            else:
                carrinho_mobile.append({"codigo": produto_atual_venda["codigo"], "nome": produto_atual_venda["nome"], "preco": produto_atual_venda["preco"], "custo": produto_atual_venda["custo"], "estoque": produto_atual_venda["estoque"], "qtd": qtd, "subtotal": subtotal})
                
            produto_atual_venda["codigo"] = ""
            venda_cod_input.value = ""
            venda_qtd_input.value = "1"
            lbl_venda_nome.value = "Adicionado!"
            lbl_venda_info.value = "Bipe o próximo item."
            atualizar_ui_carrinho()
            mostrar_mensagem("Item adicionado!", COR_VERDE_SUCESSO)

        # -------------------------------------------------------------
        # CUSTOM ITEM
        # -------------------------------------------------------------
        avulso_desc_input = ft.TextField(label="Descrição (Opcional)", value="Produto Avulso", border_color=COR_DESTAQUE)
        avulso_preco_input = ft.TextField(label="Preço do Item (R$)", keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_DESTAQUE)
        avulso_qtd_input = ft.TextField(label="Quantidade", value="1", keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_DESTAQUE)
        
        def confirmar_avulso(e):
            try:
                preco = float(avulso_preco_input.value.replace(",", "."))
                qtd = int(avulso_qtd_input.value)
                desc = avulso_desc_input.value.strip() if avulso_desc_input.value.strip() else "Produto Avulso"
                if preco <= 0 or qtd <= 0: raise ValueError
                
                carrinho_mobile.append({
                    "codigo": "AVULSO", "nome": desc, "preco": preco, 
                    "custo": 0.0, "estoque": 999, "qtd": qtd, "subtotal": preco * qtd
                })
                dialog_avulso.open = False
                page.update()
                atualizar_ui_carrinho()
                mostrar_mensagem("Avulso Adicionado!", COR_VERDE_SUCESSO)
            except ValueError:
                mostrar_mensagem("Valores inválidos!", COR_VERMELHO_ERRO)

        dialog_avulso = ft.AlertDialog(
            modal=True, title=ft.Text("🛒 Produto Avulso", weight=ft.FontWeight.BOLD),
            content=ft.Column([avulso_desc_input, avulso_preco_input, avulso_qtd_input], tight=True),
            actions=[
                ft.Container(content=ft.Text("Cancelar", color="gray", weight=ft.FontWeight.BOLD), on_click=lambda e: fechar_dialog_avulso(), padding=10),
                botao_customizado("Adicionar", COR_VERDE_SUCESSO, confirmar_avulso)
            ]
        )

        def abrir_dialog_avulso(e):
            avulso_desc_input.value = "Produto Avulso"
            avulso_preco_input.value = ""
            avulso_qtd_input.value = "1"
            page.dialog = dialog_avulso
            dialog_avulso.open = True
            page.update()

        def fechar_dialog_avulso():
            dialog_avulso.open = False
            page.update()

        # -------------------------------------------------------------
        # SEARCH BY NAME
        # -------------------------------------------------------------
        busca_nome_input = ft.TextField(label="Digite o nome...", border_color=COR_DESTAQUE)
        lista_busca_resultados = ft.ListView(height=300, spacing=5)
        
        def executar_busca_nome(e):
            termo = busca_nome_input.value.strip()
            lista_busca_resultados.controls.clear()
            lista_busca_resultados.controls.append(ft.Text("Buscando...", color="gray"))
            page.update()
            
            def buscar():
                try:
                    if termo:
                        termo_url = urllib.parse.quote(termo)
                        resp = requests.get(f"{URL}/rest/v1/produtos?nome=ilike.*{termo_url}*&select=*", headers=HEADERS, timeout=5)
                    else: resp = requests.get(f"{URL}/rest/v1/produtos?order=nome.asc&limit=30&select=*", headers=HEADERS, timeout=5)
                        
                    produtos = resp.json()
                    lista_busca_resultados.controls.clear()
                    if not produtos: lista_busca_resultados.controls.append(ft.Text("Nenhum produto encontrado.", color=COR_VERMELHO_ERRO))
                    else:
                        for p in produtos:
                            def selecionar(e, cod=p.get('codigo')):
                                dialog_busca.open = False
                                venda_cod_input.value = cod
                                processar_leitura_venda(cod)
                                page.update()
                            lista_busca_resultados.controls.append(
                                ft.ListTile(
                                    title=ft.Text(p.get('nome', ''), weight=ft.FontWeight.BOLD),
                                    subtitle=ft.Text(f"R$ {p.get('preco', 0):.2f} | Est: {p.get('estoque', 0)}"),
                                    on_click=selecionar
                                )
                            )
                    page.update()
                except Exception:
                    lista_busca_resultados.controls.clear()
                    lista_busca_resultados.controls.append(ft.Text("Erro de conexão.", color=COR_VERMELHO_ERRO))
                    page.update()
            threading.Thread(target=buscar).start()
            
        busca_nome_input.on_submit = executar_busca_nome
        
        dialog_busca = ft.AlertDialog(
            modal=True, title=ft.Text("🔍 Buscar por Nome", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=320,
                content=ft.Column([
                    ft.Row([ft.Container(content=busca_nome_input, expand=True), botao_customizado("🔍", COR_BOTAO_PRINCIPAL, executar_busca_nome)]),
                    lista_busca_resultados
                ], tight=True)
            ),
            actions=[ft.Container(content=ft.Text("Fechar", color="gray", weight=ft.FontWeight.BOLD), on_click=lambda e: fechar_dialog_busca(), padding=10)]
        )
        
        def fechar_dialog_busca():
            dialog_busca.open = False
            page.update()
            
        def abrir_dialog_busca(e):
            busca_nome_input.value = ""
            lista_busca_resultados.controls.clear()
            page.dialog = dialog_busca
            dialog_busca.open = True
            page.update()

        # -------------------------------------------------------------
        # CHECKOUT
        # -------------------------------------------------------------
        def finalizar_venda(e):
            if not carrinho_mobile: return mostrar_mensagem("O carrinho está vazio!", COR_VERMELHO_ERRO)
            total_venda = sum(i['subtotal'] for i in carrinho_mobile)
            forma_pagamento = combo_pagamento.value
            
            data_atual = datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M:%S")
            dados_venda = {"data_hora": data_atual, "subtotal": total_venda, "desconto": 0.0, "total": total_venda, "forma_pagamento": forma_pagamento}
            
            def enviar_nuvem():
                try:
                    venda_id = None
                    req_venda = requests.post(f"{URL}/rest/v1/vendas", headers=HEADERS, json=dados_venda, timeout=8)
                    
                    if not req_venda.ok:
                        dados_venda_fallback = {"data_hora": data_atual, "total": total_venda, "forma_pagamento": forma_pagamento}
                        req_venda = requests.post(f"{URL}/rest/v1/vendas", headers=HEADERS, json=dados_venda_fallback, timeout=8)

                    if req_venda.ok:
                        res_venda = req_venda.json()
                        venda_id = res_venda[0].get("id") if isinstance(res_venda, list) and len(res_venda) > 0 else None

                    if venda_id:
                        alertas_estoque = []
                        for item in carrinho_mobile:
                            dados_item = {"venda_id": venda_id, "codigo_barras": item["codigo"], "nome_produto": item["nome"], "qtd": item["qtd"], "preco_unit": item["preco"], "custo_unit": item["custo"], "subtotal": item["subtotal"]}
                            
                            req_item = requests.post(f"{URL}/rest/v1/itens_venda", headers=HEADERS, json=dados_item, timeout=8)
                            if not req_item.ok:
                                dados_item_fallback = {"venda_id": venda_id, "codigo_barras": item["codigo"], "nome_produto": item["nome"], "qtd": item["qtd"], "preco_unit": item["preco"]}
                                requests.post(f"{URL}/rest/v1/itens_venda", headers=HEADERS, json=dados_item_fallback, timeout=8)
                            
                            if item["codigo"] != "AVULSO":
                                novo_estoque = item["estoque"] - item["qtd"]
                                cod_url = urllib.parse.quote(item["codigo"])
                                req_patch = requests.patch(f"{URL}/rest/v1/produtos?codigo=eq.{cod_url}", headers=HEADERS, json={"estoque": novo_estoque}, timeout=5)
                                if req_patch.ok and novo_estoque <= 2:
                                    alertas_estoque.append(item["nome"])
                                    requests.post(f"{URL}/rest/v1/lista_compras", headers=HEADERS, json={"produto": item["nome"], "observacao": f"Estoque baixo (Restam {novo_estoque})"}, timeout=5)
                        
                        mostrar_mensagem(f"Venda Finalizada! (R$ {total_venda:.2f} via {forma_pagamento})", COR_VERDE_SUCESSO)
                        if alertas_estoque: mostrar_mensagem(f"⚠️ {len(alertas_estoque)} itens com estoque crítico.", COR_DESTAQUE)
                        
                        carrinho_mobile.clear()
                        produto_atual_venda["codigo"] = ""
                        venda_cod_input.value = ""
                        venda_qtd_input.value = "1"
                        lbl_venda_nome.value = "Nenhum produto..."
                        lbl_venda_info.value = "Aguardando código ou busca."
                        combo_pagamento.value = "Dinheiro"
                        page.update()
                        atualizar_ui_carrinho()
                    else:
                        mostrar_mensagem("Falha ao gerar ID da venda.", COR_VERMELHO_ERRO)
                except Exception as e: 
                    mostrar_mensagem("Erro de rede no checkout.", COR_VERMELHO_ERRO)
            
            mostrar_mensagem("Processando venda...", COR_BOTAO_PRINCIPAL)
            threading.Thread(target=enviar_nuvem).start()

        view_vender = ft.Column([
            ft.Container(content=ft.Text("Frente de Caixa (PDV)", size=22, weight=ft.FontWeight.BOLD, color="white"), bgcolor=COR_VERDE_SUCESSO, padding=12, alignment=ft.Alignment(0, 0)),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        venda_cod_input,
                        botao_customizado("📷", COR_BOTAO_PRINCIPAL, lambda e: abrir_leitor_codigo(venda_cod_input, ao_ler_callback=processar_leitura_venda)),
                        botao_customizado("🔍", COR_DESTAQUE, abrir_dialog_busca)
                    ]),
                    ft.Row([
                        venda_qtd_input,
                        ft.Container(content=ft.Column([lbl_venda_nome, lbl_venda_info], spacing=2), expand=True),
                        botao_customizado("➕", COR_VERDE_SUCESSO, adicionar_ao_carrinho)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    
                    botao_customizado("🛒 ADICIONAR ITEM AVULSO", COR_BOTAO_PRINCIPAL, abrir_dialog_avulso, largura=float('inf')),
                    
                    ft.Divider(color=COR_DESTAQUE),
                    ft.Text("🛒 Carrinho de Compras:", weight=ft.FontWeight.BOLD),
                    ft.Container(content=lista_carrinho, expand=True, border_radius=8, padding=5, bgcolor="#FDF8F0"),
                    ft.Divider(color=COR_DESTAQUE),
                    ft.Row([ft.Text("Total:", size=22, weight=ft.FontWeight.BOLD, color=COR_TEXTO), lbl_total_carrinho], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([ft.Text("Pagar com:", weight=ft.FontWeight.BOLD), combo_pagamento]),
                    ft.Row([
                        botao_customizado("CANCELAR", COR_VERMELHO_ERRO, cancelar_venda, expandir=True),
                        botao_customizado("FINALIZAR", COR_VERDE_SUCESSO, finalizar_venda, expandir=True)
                    ], spacing=10)
                ], spacing=10, expand=True), padding=15, expand=True
            )
        ], expand=True, spacing=0, visible=False)
        
        atualizar_ui_carrinho()

        # =====================================================================
        # TAB 3: REGISTER PRODUCT
        # =====================================================================
        aviso_conflito_txt = ft.Text("", color=COR_VERMELHO_ERRO, size=13, weight=ft.FontWeight.BOLD, visible=False)

        def verificar_codigo_existente(codigo_verificar):
            if not codigo_verificar or not str(codigo_verificar).strip():
                aviso_conflito_txt.visible = False
                page.update()
                return
            def checar():
                try:
                    cod_limpo = urllib.parse.quote(str(codigo_verificar).strip())
                    resp = requests.get(f"{URL}/rest/v1/produtos?codigo=eq.{cod_limpo}&select=*", headers=HEADERS, timeout=5)
                    existentes = resp.json()
                    if existentes and isinstance(existentes, list) and len(existentes) > 0:
                        prod_antigo = existentes[0]
                        aviso_conflito_txt.value = f"⚠️ Código já em uso: '{prod_antigo.get('nome')}' (Estoque: {prod_antigo.get('estoque')})"
                        aviso_conflito_txt.visible = True
                    else: aviso_conflito_txt.visible = False
                    page.update()
                except Exception: pass
            threading.Thread(target=checar).start()

        cad_codigo = ft.TextField(label="Código de Barras", keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_DESTAQUE, on_blur=lambda e: verificar_codigo_existente(e.control.value), on_submit=lambda e: verificar_codigo_existente(e.control.value))
        cad_nome = ft.TextField(label="Nome do Produto", border_color=COR_DESTAQUE)
        cad_custo = ft.TextField(label="Custo (R$)", keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_DESTAQUE)
        cad_preco = ft.TextField(label="Preço Venda (R$)", keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_DESTAQUE)
        cad_estoque = ft.TextField(label="Qtd. Estoque", keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_DESTAQUE)

        def limpar_campos_cadastro():
            cad_codigo.value = ""; cad_nome.value = ""; cad_custo.value = ""; cad_preco.value = ""; cad_estoque.value = ""
            aviso_conflito_txt.visible = False
            page.update()

        def gerar_codigo(e=None):
            cad_codigo.value = str(random.randint(10000000, 99999999))
            aviso_conflito_txt.visible = False
            page.update()

        def gravar_no_banco_direto(dados, modo="inserir"):
            try:
                if modo == "inserir": requests.post(f"{URL}/rest/v1/produtos", headers=HEADERS, json=dados, timeout=8)
                elif modo == "atualizar":
                    cod_url = urllib.parse.quote(str(dados["codigo"]))
                    requests.patch(f"{URL}/rest/v1/produtos?codigo=eq.{cod_url}", headers=HEADERS, json=dados, timeout=8)
                limpar_campos_cadastro()
                mostrar_mensagem(f"'{dados['nome']}' salvo com sucesso!", COR_VERDE_SUCESSO)
            except Exception: mostrar_mensagem("Erro de rede ao salvar!", COR_VERMELHO_ERRO)

        def abrir_modal_conflito(prod_existente, dados_novos):
            nome_antigo = prod_existente.get("nome", "Sem Nome")
            estoque_antigo = int(prod_existente.get("estoque", 0))
            preco_antigo = float(prod_existente.get("preco", 0.0))

            def acao_gerar_novo_codigo(e):
                dialog_conflito.open = False
                novo_cod_exclusivo = str(random.randint(10000000, 99999999))
                dados_novos["codigo"] = novo_cod_exclusivo
                mostrar_mensagem(f"Salvando com novo código ({novo_cod_exclusivo})...", COR_DESTAQUE)
                threading.Thread(target=gravar_no_banco_direto, args=(dados_novos, "inserir")).start()

            def acao_somar_estoque(e):
                dialog_conflito.open = False
                dados_novos["estoque"] = estoque_antigo + dados_novos["estoque"]
                mostrar_mensagem("Somando estoque e atualizando...", COR_DESTAQUE)
                threading.Thread(target=gravar_no_banco_direto, args=(dados_novos, "atualizar")).start()

            def acao_substituir_tudo(e):
                dialog_conflito.open = False
                mostrar_mensagem("Substituindo produto antigo...", COR_DESTAQUE)
                threading.Thread(target=gravar_no_banco_direto, args=(dados_novos, "atualizar")).start()

            dialog_conflito = ft.AlertDialog(
                modal=True, title=ft.Text("⚠️ Código Duplicado!", size=18, weight=ft.FontWeight.BOLD, color=COR_VERMELHO_ERRO),
                content=ft.Container(
                    width=310,
                    content=ft.Column([
                        ft.Text(f"O código {dados_novos['codigo']} já existe no sistema:", size=14),
                        ft.Container(padding=10, bgcolor="#FFF3CD", border_radius=8, content=ft.Column([ft.Text(f"📦 Atual: {nome_antigo}", weight=ft.FontWeight.BOLD, color=COR_TEXTO), ft.Text(f"💰 Preço: R$ {preco_antigo:.2f} | Estoque: {estoque_antigo}", size=13, color="#856404")], spacing=4)),
                        ft.Text(f"Você está tentando salvar: '{dados_novos['nome']}'", size=14, weight=ft.FontWeight.BOLD),
                        ft.Divider(), ft.Text("O que deseja fazer?", size=14, color="gray"),
                        botao_customizado("🎲 Gerar Novo Código (Manter os Dois)", COR_VERDE_SUCESSO, acao_gerar_novo_codigo, largura=300),
                        botao_customizado(f"➕ Somar Estoque ({estoque_antigo} + {dados_novos['estoque']} = {estoque_antigo + dados_novos['estoque']})", COR_DESTAQUE, acao_somar_estoque, largura=300),
                        botao_customizado("🔄 Substituir Produto Antigo", COR_VERMELHO_ERRO, acao_substituir_tudo, largura=300),
                    ], spacing=10, tight=True)
                ), actions=[ft.Container(content=ft.Text("Cancelar", color="gray", weight=ft.FontWeight.BOLD), on_click=lambda e: [setattr(dialog_conflito, 'open', False), page.update()], padding=10)]
            )
            page.dialog = dialog_conflito
            dialog_conflito.open = True
            page.update()

        def salvar_produto(e):
            codigo = cad_codigo.value.strip() if cad_codigo.value else ""
            nome = cad_nome.value.strip() if cad_nome.value else ""
            if not codigo or not nome: return mostrar_mensagem("Código e Nome são obrigatórios!", COR_VERMELHO_ERRO)
            try:
                custo = float(cad_custo.value.replace(',', '.')) if cad_custo.value else 0.0
                preco_digitado = float(cad_preco.value.replace(',', '.')) if cad_preco.value else 0.0
                if preco_digitado == 0.0 and custo > 0:
                    preco_base = custo * 2.0
                    centavos = int(round(preco_base * 100))
                    ultimo_digito = centavos % 10
                    preco_final = (centavos + (9 - ultimo_digito)) / 100.0 if ultimo_digito < 9 else preco_base
                else: preco_final = preco_digitado
                estoque = int(cad_estoque.value) if cad_estoque.value else 0
                dados = {"codigo": codigo, "nome": nome, "custo": custo, "preco": preco_final, "estoque": estoque}
                def processo_verificar_e_salvar():
                    try:
                        cod_url = urllib.parse.quote(codigo)
                        resp = requests.get(f"{URL}/rest/v1/produtos?codigo=eq.{cod_url}&select=*", headers=HEADERS, timeout=8)
                        existentes = resp.json()
                        if existentes and isinstance(existentes, list) and len(existentes) > 0: abrir_modal_conflito(existentes[0], dados)
                        else: gravar_no_banco_direto(dados, "inserir")
                    except Exception: mostrar_mensagem("Erro de rede verificando banco!", COR_VERMELHO_ERRO)
                mostrar_mensagem("Verificando código na nuvem...", COR_DESTAQUE)
                threading.Thread(target=processo_verificar_e_salvar).start()
            except Exception: mostrar_mensagem("Valor inválido! Use apenas números.", COR_VERMELHO_ERRO)

        view_cadastrar = ft.Column([
            ft.Container(content=ft.Text("Cadastro Rápido", size=24, weight=ft.FontWeight.BOLD, color="white"), bgcolor=COR_DESTAQUE, padding=15, alignment=ft.Alignment(0, 0)),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(content=cad_codigo, expand=True),
                        botao_customizado("📷", COR_BOTAO_PRINCIPAL, lambda e: abrir_leitor_codigo(cad_codigo, ao_ler_callback=verificar_codigo_existente)),
                        botao_customizado("🎲", COR_DESTAQUE, gerar_codigo)
                    ]),
                    aviso_conflito_txt, cad_nome, cad_custo, cad_preco, cad_estoque,
                    botao_customizado("💾 SALVAR PRODUTO", COR_VERDE_SUCESSO, salvar_produto, altura=50, expandir=True)
                ], spacing=15, scroll=ft.ScrollMode.AUTO), padding=20, expand=True
            )
        ], expand=True, spacing=0, visible=False)

        # =====================================================================
        # TAB 4: RESTOCK LIST
        # =====================================================================
        compra_nome = ft.TextField(label="O que está faltando?", border_color=COR_DESTAQUE)
        compra_obs = ft.TextField(label="Obs / Qtd (Opcional)", border_color=COR_DESTAQUE)
        lista_compras_view = ft.ListView(expand=True, spacing=10)

        def carregar_compras():
            def processo_compras():
                try:
                    resp = requests.get(f"{URL}/rest/v1/lista_compras?select=*&order=id.desc", headers=HEADERS, timeout=8)
                    lista_compras_view.controls.clear()
                    itens = resp.json()
                    if not itens: lista_compras_view.controls.append(ft.Text("Lista de compras vazia.", color="gray", text_align=ft.TextAlign.CENTER))
                    else:
                        for c in itens:
                            lista_compras_view.controls.append(
                                ft.Card(
                                    color=COR_PAINEL, elevation=2,
                                    content=ft.ListTile(leading=ft.Text("🛍️", size=20), title=ft.Text(c.get('produto', ''), weight=ft.FontWeight.BOLD, color=COR_TEXTO), subtitle=ft.Text(c.get('observacao', '') or "Sem anotações"), trailing=ft.Container(content=ft.Text("❌", size=18, color=COR_VERMELHO_ERRO), on_click=deletar_compra, data=c.get('id'), padding=5))
                                )
                            )
                    page.update()
                except Exception: pass
            threading.Thread(target=processo_compras).start()

        def adicionar_compra(e):
            if not compra_nome.value or not compra_nome.value.strip(): return mostrar_mensagem("Informe o nome do produto!", COR_VERMELHO_ERRO)
            dados = {"produto": compra_nome.value.strip(), "observacao": compra_obs.value.strip() if compra_obs.value else ""}
            compra_nome.value = ""; compra_obs.value = ""
            page.update()
            def processo_add():
                try:
                    requests.post(f"{URL}/rest/v1/lista_compras", headers=HEADERS, json=dados, timeout=8)
                    mostrar_mensagem("Adicionado à lista!", COR_VERDE_SUCESSO)
                    carregar_compras()
                except Exception: mostrar_mensagem("Erro ao adicionar.", COR_VERMELHO_ERRO)
            threading.Thread(target=processo_add).start()

        def deletar_compra(e):
            item_id = e.control.data
            def processo_del():
                try:
                    requests.delete(f"{URL}/rest/v1/lista_compras?id=eq.{item_id}", headers=HEADERS, timeout=8)
                    mostrar_mensagem("Item removido!", COR_VERDE_SUCESSO)
                    carregar_compras()
                except Exception: pass
            threading.Thread(target=processo_del).start()

        view_compras = ft.Column([
            ft.Container(content=ft.Text("Lista de Compras", size=24, weight=ft.FontWeight.BOLD, color="white"), bgcolor=COR_BOTAO_PRINCIPAL, padding=15, alignment=ft.Alignment(0, 0)),
            ft.Container(
                content=ft.Column([
                    compra_nome, compra_obs,
                    botao_customizado("➕ ADICIONAR", COR_DESTAQUE, adicionar_compra, altura=45, expandir=True),
                    ft.Divider(color=COR_DESTAQUE), lista_compras_view
                ], spacing=10, expand=True), padding=20, expand=True
            )
        ], expand=True, spacing=0, visible=False)

        # =====================================================================
        # BOTTOM NAVIGATION BAR
        # =====================================================================
        def mudar_aba(e):
            idx = e.control.selected_index
            view_estoque.visible = (idx == 0)
            view_vender.visible = (idx == 1)
            view_cadastrar.visible = (idx == 2)
            view_compras.visible = (idx == 3)
            if idx == 0: threading.Thread(target=carregar_estoque).start()
            elif idx == 3: carregar_compras()
            page.update()

        # Correção Blindada Flet 1.0
        page.navigation_bar = ft.NavigationBar(
            selected_index=0, bgcolor=COR_PAINEL, indicator_color=COR_FUNDO, on_change=mudar_aba,
            destinations=[
                ft.NavigationBarDestination(label="📦 Consulta"),
                ft.NavigationBarDestination(label="💰 Vender"),
                ft.NavigationBarDestination(label="➕ Cadastrar"),
                ft.NavigationBarDestination(label="🛒 Compras"),
            ]
        )

        page.add(view_estoque, view_vender, view_cadastrar, view_compras)
        threading.Thread(target=carregar_estoque).start()
        
    except Exception:
        page.add(ft.Container(padding=20, content=ft.Column([ft.Text("🚨 ERRO CRÍTICO NO APLICATIVO", color="red", weight=ft.FontWeight.BOLD, size=20), ft.Text(str(traceback.format_exc()), color="black", size=12)], scroll=ft.ScrollMode.AUTO)))
        page.update()

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 8080))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=porta, assets_dir="assets")
