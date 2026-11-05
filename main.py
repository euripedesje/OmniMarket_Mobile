import flet as ft
import requests
import random
import threading
import traceback
import urllib.parse
from datetime import datetime, timezone, timedelta
import os

# =========================================================================
# CLOUD CREDENTIALS & TIMEZONE (OMNIMARKET POS)
# =========================================================================
URL = "https://vjytmsiicmmfynlolxrn.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZqeXRtc2lpY21tZnlubG9seHJuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTM4MjI2MTUsImV4cCI6MjEwOTM5ODYxNX0.aavTQjTgsAK94cxWSxRoiMHAzg9f2EpCURgu9IVc6wI"
FUSO_BR = timezone(timedelta(hours=-3))

HEADERS = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# =========================================================================
# TECH CORPORATE PALETTE - OMNIMARKET POS
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
                label="Scanned code or type here", autofocus=True,
                keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_DESTAQUE,
                on_submit=lambda e: confirmar_codigo(e.control.value)
            )

            def confirmar_codigo(valor):
                if valor and str(valor).strip():
                    codigo_final = str(valor).strip()
                    campo_destino.value = codigo_final
                    dialog_camera.open = False
                    page.update()
                    mostrar_mensagem(f"Code: {codigo_final}", COR_VERDE_SUCESSO)
                    if ao_ler_callback: ao_ler_callback(codigo_final)

            def colar_da_area_transferencia(e):
                try:
                    texto_colado = page.get_clipboard()
                    if texto_colado and str(texto_colado).strip(): confirmar_codigo(texto_colado)
                    else: mostrar_mensagem("Clipboard is empty!", COR_VERMELHO_ERRO)
                except Exception: mostrar_mensagem("Please paste manually.", COR_DESTAQUE)

            def abrir_camera_externa(e): page.launch_url("https://scanapp.org/")
            def fechar_dialog(e=None):
                dialog_camera.open = False
                page.update()

            dialog_camera = ft.AlertDialog(
                modal=True,
                title=ft.Text("📷 Scan Barcode", size=18, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
                content=ft.Container(
                    width=310,
                    content=ft.Column([
                        ft.Button("📷 OPEN CAMERA SCANNER", bgcolor=COR_BOTAO_PRINCIPAL, color="white", height=45, width=300, on_click=abrir_camera_externa),
                        ft.Button("📋 PASTE SCANNED CODE", bgcolor=COR_DESTAQUE, color="white", height=45, width=300, on_click=colar_da_area_transferencia),
                        ft.Divider(color=COR_DESTAQUE), input_manual,
                    ], spacing=10, tight=True)
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=fechar_dialog),
                    ft.Button("Confirm", bgcolor=COR_VERDE_SUCESSO, color="white", on_click=lambda e: confirmar_codigo(input_manual.value))
                ], actions_alignment=ft.MainAxisAlignment.END
            )
            page.dialog = dialog_camera
            dialog_camera.open = True
            page.update()

        # =====================================================================
        # TAB 1: INVENTORY CHECK
        # =====================================================================
        lista_produtos = ft.ListView(expand=True, spacing=10, padding=10)
        busca_input = ft.TextField(
            label="🔍 Search name or barcode", expand=True, border_color=COR_DESTAQUE, 
            focused_border_color=COR_BOTAO_PRINCIPAL, on_submit=lambda e: threading.Thread(target=carregar_estoque, args=(e.control.value,)).start()
        )

        def carregar_estoque(termo=""):
            lista_produtos.controls.clear()
            lista_produtos.controls.append(ft.Text("Syncing...", color="gray", text_align=ft.TextAlign.CENTER))
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
                
                if not produtos: lista_produtos.controls.append(ft.Text("No products found.", size=16, text_align=ft.TextAlign.CENTER))
                else:
                    for p in produtos:
                        estoque_atual = p.get('estoque', 0)
                        lista_produtos.controls.append(
                            ft.Card(
                                content=ft.Container(
                                    padding=15,
                                    content=ft.Column([
                                        ft.Text(p.get('nome', 'No Name'), weight=ft.FontWeight.BOLD, size=18, color=COR_TEXTO),
                                        ft.Row([
                                            ft.Text(f"SKU: {p.get('codigo', '')}", color="gray", size=14),
                                            ft.Text(f"Stock: {estoque_atual}", color=COR_VERMELHO_ERRO if estoque_atual <= 2 else COR_VERDE_SUCESSO, weight=ft.FontWeight.BOLD, size=14)
                                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                        ft.Text(f"$ {float(p.get('preco', 0.0)):.2f}", size=20, color=COR_DESTAQUE, weight=ft.FontWeight.BOLD)
                                    ])
                                ), color=COR_PAINEL, elevation=3
                            )
                        )
            except Exception:
                lista_produtos.controls.clear()
                lista_produtos.controls.append(ft.Text("Connection error.", color=COR_VERMELHO_ERRO, text_align=ft.TextAlign.CENTER))
            page.update()

        view_estoque = ft.Column([
            topo_app,
            ft.Container(
                content=ft.Row([
                    busca_input,
                    ft.Button("📷", on_click=lambda e: abrir_leitor_codigo(busca_input, ao_ler_callback=lambda cod: threading.Thread(target=carregar_estoque, args=(cod,)).start())),
                    ft.Button("🔍", on_click=lambda e: threading.Thread(target=carregar_estoque, args=(busca_input.value,)).start())
                ]), padding=10
            ), lista_produtos
        ], expand=True, spacing=0, visible=True)

        # =====================================================================
        # TAB 2: MOBILE POS (CART, SEARCH, CUSTOM ITEM)
        # =====================================================================
        carrinho_mobile = []
        produto_atual_venda = {"codigo": "", "nome": "", "preco": 0.0, "custo": 0.0, "estoque": 0}
        
        venda_cod_input = ft.TextField(label="Product Barcode", border_color=COR_DESTAQUE, expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        venda_qtd_input = ft.TextField(label="Qty", value="1", width=60, keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_DESTAQUE, text_align=ft.TextAlign.CENTER)
        
        lbl_venda_nome = ft.Text("No product selected...", size=16, weight=ft.FontWeight.BOLD, color=COR_TEXTO, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1)
        lbl_venda_info = ft.Text("Waiting for scan or search.", size=13, color="gray")
        
        lista_carrinho = ft.ListView(expand=True, spacing=5)
        lbl_total_carrinho = ft.Text("$ 0.00", size=26, weight=ft.FontWeight.BOLD, color=COR_VERDE_SUCESSO)
        
        combo_pagamento = ft.Dropdown(
            options=[ft.dropdown.Option("Cash"), ft.dropdown.Option("Apple/Google Pay"), ft.dropdown.Option("Credit Card"), ft.dropdown.Option("Debit Card"), ft.dropdown.Option("Store Credit")],
            value="Cash", border_color=COR_DESTAQUE, expand=True, height=50
        )

        def atualizar_ui_carrinho():
            lista_carrinho.controls.clear()
            total_venda = 0.0
            if not carrinho_mobile: lista_carrinho.controls.append(ft.Text("Cart is empty.", color="gray", text_align=ft.TextAlign.CENTER))
            else:
                for idx, item in enumerate(carrinho_mobile):
                    total_venda += item['subtotal']
                    lista_carrinho.controls.append(
                        ft.Card(
                            elevation=1, color=COR_PAINEL,
                            content=ft.ListTile(
                                title=ft.Text(f"{item['qtd']}x {item['nome']}", weight=ft.FontWeight.BOLD, size=14),
                                subtitle=ft.Text(f"$ {item['preco']:.2f} ea | Sub: $ {item['subtotal']:.2f}", size=13),
                                trailing=ft.Button("❌", on_click=lambda e, i=idx: remover_do_carrinho(i))
                            )
                        )
                    )
            lbl_total_carrinho.value = f"$ {total_venda:.2f}"
            page.update()

        def remover_do_carrinho(index):
            if 0 <= index < len(carrinho_mobile):
                removido = carrinho_mobile.pop(index)
                mostrar_mensagem(f"Removed: {removido['nome']}", COR_DESTAQUE)
                atualizar_ui_carrinho()

        def cancelar_venda(e=None):
            carrinho_mobile.clear()
            produto_atual_venda["codigo"] = ""
            venda_cod_input.value = ""
            venda_qtd_input.value = "1"
            lbl_venda_nome.value = "No product selected..."
            lbl_venda_info.value = "Waiting for scan or search."
            combo_pagamento.value = "Cash"
            atualizar_ui_carrinho()
            mostrar_mensagem("Sale cancelled.", COR_VERMELHO_ERRO)

        def processar_leitura_venda(codigo):
            cod_limpo = str(codigo).strip()
            if not cod_limpo: return
            lbl_venda_nome.value = "Searching..."
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
                        lbl_venda_info.value = f"$ {produto_atual_venda['preco']:.2f} | Stock: {produto_atual_venda['estoque']}"
                        mostrar_mensagem("Item ready to add!", COR_BOTAO_PRINCIPAL)
                    else:
                        lbl_venda_nome.value = "Not registered!"
                        lbl_venda_info.value = "Check barcode."
                        produto_atual_venda["codigo"] = ""
                    page.update()
                except Exception:
                    lbl_venda_nome.value = "Network Error"
                    page.update()
            threading.Thread(target=buscar).start()

        venda_cod_input.on_submit = lambda e: processar_leitura_venda(e.control.value)

        def adicionar_ao_carrinho(e):
            if not produto_atual_venda["codigo"]: return mostrar_mensagem("Scan or search an item!", COR_VERMELHO_ERRO)
            try:
                qtd = int(venda_qtd_input.value)
                if qtd <= 0: raise ValueError
            except: return mostrar_mensagem("Invalid quantity!", COR_VERMELHO_ERRO)
            
            qtd_ja_no_carrinho = sum(i['qtd'] for i in carrinho_mobile if i['codigo'] == produto_atual_venda["codigo"])
            if (qtd + qtd_ja_no_carrinho) > produto_atual_venda["estoque"]:
                return mostrar_mensagem(f"Insufficient stock! (Avail: {produto_atual_venda['estoque']})", COR_VERMELHO_ERRO)
                
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
            lbl_venda_nome.value = "Added!"
            lbl_venda_info.value = "Scan the next item."
            atualizar_ui_carrinho()
            mostrar_mensagem("Added to cart!", COR_VERDE_SUCESSO)

        # -------------------------------------------------------------
        # CUSTOM ITEM
        # -------------------------------------------------------------
        avulso_desc_input = ft.TextField(label="Description (Optional)", value="Custom Item", border_color=COR_DESTAQUE)
        avulso_preco_input = ft.TextField(label="Item Price ($)", keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_DESTAQUE)
        avulso_qtd_input = ft.TextField(label="Quantity", value="1", keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_DESTAQUE)
        
        def confirmar_avulso(e):
            try:
                preco = float(avulso_preco_input.value.replace(",", "."))
                qtd = int(avulso_qtd_input.value)
                desc = avulso_desc_input.value.strip() if avulso_desc_input.value.strip() else "Custom Item"
                if preco <= 0 or qtd <= 0: raise ValueError
                
                carrinho_mobile.append({
                    "codigo": "AVULSO", "nome": desc, "preco": preco, 
                    "custo": 0.0, "estoque": 999, "qtd": qtd, "subtotal": preco * qtd
                })
                dialog_avulso.open = False
                page.update()
                atualizar_ui_carrinho()
                mostrar_mensagem("Custom Item Added!", COR_VERDE_SUCESSO)
            except ValueError:
                mostrar_mensagem("Invalid values!", COR_VERMELHO_ERRO)

        dialog_avulso = ft.AlertDialog(
            modal=True, title=ft.Text("🛒 Custom Item", weight=ft.FontWeight.BOLD),
            content=ft.Column([avulso_desc_input, avulso_preco_input, avulso_qtd_input], tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: fechar_dialog_avulso()),
                ft.Button("Add to Cart", bgcolor=COR_VERDE_SUCESSO, color="white", on_click=confirmar_avulso)
            ]
        )

        def abrir_dialog_avulso(e):
            avulso_desc_input.value = "Custom Item"
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
        busca_nome_input = ft.TextField(label="Type name here...", border_color=COR_DESTAQUE)
        lista_busca_resultados = ft.ListView(height=300, spacing=5)
        
        def executar_busca_nome(e):
            termo = busca_nome_input.value.strip()
            lista_busca_resultados.controls.clear()
            lista_busca_resultados.controls.append(ft.Text("Searching...", color="gray"))
            page.update()
            
            def buscar():
                try:
                    if termo:
                        termo_url = urllib.parse.quote(termo)
                        resp = requests.get(f"{URL}/rest/v1/produtos?nome=ilike.*{termo_url}*&select=*", headers=HEADERS, timeout=5)
                    else: resp = requests.get(f"{URL}/rest/v1/produtos?order=nome.asc&limit=30&select=*", headers=HEADERS, timeout=5)
                        
                    produtos = resp.json()
                    lista_busca_resultados.controls.clear()
                    if not produtos: lista_busca_resultados.controls.append(ft.Text("No products found.", color=COR_VERMELHO_ERRO))
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
                                    subtitle=ft.Text(f"$ {p.get('preco', 0):.2f} | Stock: {p.get('estoque', 0)}"),
                                    on_click=selecionar
                                )
                            )
                    page.update()
                except Exception:
                    lista_busca_resultados.controls.clear()
                    lista_busca_resultados.controls.append(ft.Text("Connection error.", color=COR_VERMELHO_ERRO))
                    page.update()
            threading.Thread(target=buscar).start()
            
        busca_nome_input.on_submit = executar_busca_nome
        
        dialog_busca = ft.AlertDialog(
            modal=True, title=ft.Text("🔍 Search by Name", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=320,
                content=ft.Column([
                    ft.Row([ft.Container(content=busca_nome_input, expand=True), ft.Button("🔍", bgcolor=COR_BOTAO_PRINCIPAL, color="white", on_click=executar_busca_nome)]),
                    lista_busca_resultados
                ], tight=True)
            ),
            actions=[ft.TextButton("Close", on_click=lambda e: fechar_dialog_busca())]
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
            if not carrinho_mobile: return mostrar_mensagem("Cart is empty!", COR_VERMELHO_ERRO)
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
                                    requests.post(f"{URL}/rest/v1/lista_compras", headers=HEADERS, json={"produto": item["nome"], "observacao": f"Low stock (Remaining {novo_estoque})"}, timeout=5)
                        
                        mostrar_mensagem(f"Checkout Complete! ($ {total_venda:.2f} via {forma_pagamento})", COR_VERDE_SUCESSO)
                        if alertas_estoque: mostrar_mensagem(f"⚠️ {len(alertas_estoque)} items are low on stock.", COR_DESTAQUE)
                        
                        carrinho_mobile.clear()
                        produto_atual_venda["codigo"] = ""
                        venda_cod_input.value = ""
                        venda_qtd_input.value = "1"
                        lbl_venda_nome.value = "No product selected..."
                        lbl_venda_info.value = "Waiting for scan or search."
                        combo_pagamento.value = "Cash"
                        page.update()
                        atualizar_ui_carrinho()
                    else:
                        mostrar_mensagem("Failed to create sale ID.", COR_VERMELHO_ERRO)
                except Exception as e: 
                    mostrar_mensagem("Network error during checkout.", COR_VERMELHO_ERRO)
            
            mostrar_mensagem("Processing checkout...", COR_BOTAO_PRINCIPAL)
            threading.Thread(target=enviar_nuvem).start()

        view_vender = ft.Column([
            ft.Container(content=ft.Text("Point of Sale (POS)", size=22, weight=ft.FontWeight.BOLD, color="white"), bgcolor=COR_VERDE_SUCESSO, padding=12, alignment=ft.Alignment(0, 0)),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        venda_cod_input,
                        ft.Button("📷", on_click=lambda e: abrir_leitor_codigo(venda_cod_input, ao_ler_callback=processar_leitura_venda)),
                        ft.Button("🔍", on_click=abrir_dialog_busca)
                    ]),
                    ft.Row([
                        venda_qtd_input,
                        ft.Container(content=ft.Column([lbl_venda_nome, lbl_venda_info], spacing=2), expand=True),
                        ft.Button("➕", bgcolor=COR_VERDE_SUCESSO, color="white", on_click=adicionar_ao_carrinho)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    
                    ft.Button("🛒 ADD CUSTOM ITEM", width=float('inf'), height=40, bgcolor=COR_BOTAO_PRINCIPAL, color="white", on_click=abrir_dialog_avulso),
                    
                    ft.Divider(color=COR_DESTAQUE),
                    ft.Text("🛒 Shopping Cart:", weight=ft.FontWeight.BOLD),
                    # Correção Flet 1.0: Remover borda problemática. 
                    ft.Container(content=lista_carrinho, expand=True, border_radius=8, padding=5, bgcolor="#FDF8F0"),
                    ft.Divider(color=COR_DESTAQUE),
                    ft.Row([ft.Text("Total:", size=22, weight=ft.FontWeight.BOLD, color=COR_TEXTO), lbl_total_carrinho], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([ft.Text("Tender:", weight=ft.FontWeight.BOLD), combo_pagamento]),
                    ft.Row([
                        ft.Button("CANCEL", expand=True, height=50, bgcolor=COR_VERMELHO_ERRO, color="white", on_click=cancelar_venda),
                        ft.Button("CHECKOUT", expand=True, height=50, bgcolor=COR_VERDE_SUCESSO, color="white", on_click=finalizar_venda)
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
                        aviso_conflito_txt.value = f"⚠️ Barcode already used by: '{prod_antigo.get('nome')}' (Stk: {prod_antigo.get('estoque')})"
                        aviso_conflito_txt.visible = True
                    else: aviso_conflito_txt.visible = False
                    page.update()
                except Exception: pass
            threading.Thread(target=checar).start()

        cad_codigo = ft.TextField(label="Barcode", keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_DESTAQUE, on_blur=lambda e: verificar_codigo_existente(e.control.value), on_submit=lambda e: verificar_codigo_existente(e.control.value))
        cad_nome = ft.TextField(label="Product Name", border_color=COR_DESTAQUE)
        cad_custo = ft.TextField(label="Cost ($)", keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_DESTAQUE)
        cad_preco = ft.TextField(label="Selling Price ($)", keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_DESTAQUE)
        cad_estoque = ft.TextField(label="Quantity in Stock", keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_DESTAQUE)

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
                mostrar_mensagem(f"'{dados['nome']}' saved successfully!", COR_VERDE_SUCESSO)
            except Exception: mostrar_mensagem("Network error while saving!", COR_VERMELHO_ERRO)

        def abrir_modal_conflito(prod_existente, dados_novos):
            nome_antigo = prod_existente.get("nome", "No Name")
            estoque_antigo = int(prod_existente.get("estoque", 0))
            preco_antigo = float(prod_existente.get("preco", 0.0))

            def acao_gerar_novo_codigo(e):
                dialog_conflito.open = False
                novo_cod_exclusivo = str(random.randint(10000000, 99999999))
                dados_novos["codigo"] = novo_cod_exclusivo
                mostrar_mensagem(f"Saving with new barcode ({novo_cod_exclusivo})...", COR_DESTAQUE)
                threading.Thread(target=gravar_no_banco_direto, args=(dados_novos, "inserir")).start()

            def acao_somar_estoque(e):
                dialog_conflito.open = False
                dados_novos["estoque"] = estoque_antigo + dados_novos["estoque"]
                mostrar_mensagem("Adding stock and updating...", COR_DESTAQUE)
                threading.Thread(target=gravar_no_banco_direto, args=(dados_novos, "atualizar")).start()

            def acao_substituir_tudo(e):
                dialog_conflito.open = False
                mostrar_mensagem("Overwriting previous product...", COR_DESTAQUE)
                threading.Thread(target=gravar_no_banco_direto, args=(dados_novos, "atualizar")).start()

            dialog_conflito = ft.AlertDialog(
                modal=True, title=ft.Text("⚠️ Duplicate Barcode!", size=18, weight=ft.FontWeight.BOLD, color=COR_VERMELHO_ERRO),
                content=ft.Container(
                    width=310,
                    content=ft.Column([
                        ft.Text(f"The barcode {dados_novos['codigo']} is already in the system:", size=14),
                        ft.Container(padding=10, bgcolor="#FFF3CD", border_radius=8, content=ft.Column([ft.Text(f"📦 Current: {nome_antigo}", weight=ft.FontWeight.BOLD, color=COR_TEXTO), ft.Text(f"💰 Price: $ {preco_antigo:.2f} | Stock: {estoque_antigo}", size=13, color="#856404")], spacing=4)),
                        ft.Text(f"You are trying to save: '{dados_novos['nome']}'", size=14, weight=ft.FontWeight.BOLD),
                        ft.Divider(), ft.Text("What do you want to do?", size=14, color="gray"),
                        ft.Button("🎲 Generate New Barcode (Keep Both)", bgcolor=COR_VERDE_SUCESSO, color="white", width=300, on_click=acao_gerar_novo_codigo),
                        ft.Button(f"➕ Add Stock ({estoque_antigo} + {dados_novos['estoque']} = {estoque_antigo + dados_novos['estoque']})", bgcolor=COR_DESTAQUE, color="white", width=300, on_click=acao_somar_estoque),
                        ft.Button("🔄 Overwrite Old Product", bgcolor=COR_VERMELHO_ERRO, color="white", width=300, on_click=acao_substituir_tudo),
                    ], spacing=10, tight=True)
                ), actions=[ft.TextButton("Cancel", on_click=lambda e: [setattr(dialog_conflito, 'open', False), page.update()])]
            )
            page.dialog = dialog_conflito
            dialog_conflito.open = True
            page.update()

        def salvar_produto(e):
            codigo = cad_codigo.value.strip() if cad_codigo.value else ""
            nome = cad_nome.value.strip() if cad_nome.value else ""
            if not codigo or not nome: return mostrar_mensagem("Barcode and Name are required!", COR_VERMELHO_ERRO)
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
                    except Exception: mostrar_mensagem("Network error while checking database!", COR_VERMELHO_ERRO)
                mostrar_mensagem("Verifying barcode in cloud...", COR_DESTAQUE)
                threading.Thread(target=processo_verificar_e_salvar).start()
            except Exception: mostrar_mensagem("Value error! Use numbers only.", COR_VERMELHO_ERRO)

        view_cadastrar = ft.Column([
            ft.Container(content=ft.Text("Quick Register", size=24, weight=ft.FontWeight.BOLD, color="white"), bgcolor=COR_DESTAQUE, padding=15, alignment=ft.Alignment(0, 0)),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(content=cad_codigo, expand=True),
                        ft.Button("📷", on_click=lambda e: abrir_leitor_codigo(cad_codigo, ao_ler_callback=verificar_codigo_existente)),
                        ft.Button("🎲", on_click=gerar_codigo)
                    ]),
                    aviso_conflito_txt, cad_nome, cad_custo, cad_preco, cad_estoque,
                    ft.Button("💾 SAVE PRODUCT", height=50, bgcolor=COR_VERDE_SUCESSO, color="white", on_click=salvar_produto, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
                ], spacing=15, scroll=ft.ScrollMode.AUTO), padding=20, expand=True
            )
        ], expand=True, spacing=0, visible=False)

        # =====================================================================
        # TAB 4: RESTOCK LIST
        # =====================================================================
        compra_nome = ft.TextField(label="What is missing in store?", border_color=COR_DESTAQUE)
        compra_obs = ft.TextField(label="Notes / Qty (Optional)", border_color=COR_DESTAQUE)
        lista_compras_view = ft.ListView(expand=True, spacing=10)

        def carregar_compras():
            def processo_compras():
                try:
                    resp = requests.get(f"{URL}/rest/v1/lista_compras?select=*&order=id.desc", headers=HEADERS, timeout=8)
                    lista_compras_view.controls.clear()
                    itens = resp.json()
                    if not itens: lista_compras_view.controls.append(ft.Text("Restock list is empty.", color="gray", text_align=ft.TextAlign.CENTER))
                    else:
                        for c in itens:
                            lista_compras_view.controls.append(
                                ft.Card(
                                    color=COR_PAINEL, elevation=2,
                                    content=ft.ListTile(leading=ft.Text("🛍️", size=20), title=ft.Text(c.get('produto', ''), weight=ft.FontWeight.BOLD, color=COR_TEXTO), subtitle=ft.Text(c.get('observacao', '') or "No notes"), trailing=ft.Button("❌", on_click=deletar_compra, data=c.get('id')))
                                )
                            )
                    page.update()
                except Exception: pass
            threading.Thread(target=processo_compras).start()

        def adicionar_compra(e):
            if not compra_nome.value or not compra_nome.value.strip(): return mostrar_mensagem("Enter the missing product name!", COR_VERMELHO_ERRO)
            dados = {"produto": compra_nome.value.strip(), "observacao": compra_obs.value.strip() if compra_obs.value else ""}
            compra_nome.value = ""; compra_obs.value = ""
            page.update()
            def processo_add():
                try:
                    requests.post(f"{URL}/rest/v1/lista_compras", headers=HEADERS, json=dados, timeout=8)
                    mostrar_mensagem("Added to restock list!", COR_VERDE_SUCESSO)
                    carregar_compras()
                except Exception: mostrar_mensagem("Error adding item.", COR_VERMELHO_ERRO)
            threading.Thread(target=processo_add).start()

        def deletar_compra(e):
            item_id = e.control.data
            def processo_del():
                try:
                    requests.delete(f"{URL}/rest/v1/lista_compras?id=eq.{item_id}", headers=HEADERS, timeout=8)
                    mostrar_mensagem("Item removed from list!", COR_VERDE_SUCESSO)
                    carregar_compras()
                except Exception: pass
            threading.Thread(target=processo_del).start()

        view_compras = ft.Column([
            ft.Container(content=ft.Text("Restock List", size=24, weight=ft.FontWeight.BOLD, color="white"), bgcolor=COR_BOTAO_PRINCIPAL, padding=15, alignment=ft.Alignment(0, 0)),
            ft.Container(
                content=ft.Column([
                    compra_nome, compra_obs,
                    ft.Button("➕ ADD TO LIST", height=45, bgcolor=COR_DESTAQUE, color="white", on_click=adicionar_compra, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))),
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

        page.navigation_bar = ft.NavigationBar(
            selected_index=0, bgcolor=COR_PAINEL, indicator_color=COR_FUNDO, on_change=mudar_aba,
            destinations=[
                ft.NavigationDestination(label="📦 Inventory"),
                ft.NavigationDestination(label="💰 POS"),
                ft.NavigationDestination(label="➕ Register"),
                ft.NavigationDestination(label="🛒 Restock"),
            ]
        )

        page.add(view_estoque, view_vender, view_cadastrar, view_compras)
        threading.Thread(target=carregar_estoque).start()
        
    except Exception:
        page.add(ft.Container(padding=20, content=ft.Column([ft.Text("🚨 CRITICAL APP ERROR", color="red", weight=ft.FontWeight.BOLD, size=20), ft.Text(str(traceback.format_exc()), color="black", size=12)], scroll=ft.ScrollMode.AUTO)))
        page.update()

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 8080))
    ft.run(main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=porta, assets_dir="assets")
